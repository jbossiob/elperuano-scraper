// analyze.ts
import fs from "fs";
import path from "path";
import pdf from "pdf-parse";
import PDFDocument from "pdfkit";
import { GoogleGenAI, Type } from "@google/genai";

// ----------------------------
// Tipos de datos
// ----------------------------
enum Relevance {
  ALTA = "Alta",
  MEDIA = "Media",
  BAJA = "Baja",
  NINGUNA = "Ninguna",
}

type Norm = {
  sector: string;
  normId: string;
  title: string;
  publicationDate: string;
  summary: string;
  relevanceToWaterSector: Relevance;
  pageNumber: number;
};

type Appointment = {
  institution: string;
  personName: string;
  position: string;
  summary: string;
};

type AnalysisResult = {
  gazetteDate: string;
  norms: Norm[];
  designatedAppointments: Appointment[];
  concludedAppointments: Appointment[];
};

// ----------------------------
// 1. Extraer texto del PDF
// ----------------------------
async function extractPagesText(
  pdfPath: string
): Promise<Array<{ page: number; text: string }>> {
  const buffer = fs.readFileSync(pdfPath);
  const data = await pdf(buffer);

  // pdf-parse suele usar caracteres de salto de página \f
  const rawText = data.text;
  const pages = rawText.split("\f");

  return pages
    .map((text, index) => ({
      page: index + 1,
      text: text.trim(),
    }))
    .filter((p) => p.text.length > 0);
}

// ----------------------------
// 2. Llamar a Gemini
// ----------------------------
if (!process.env.GEMINI_API_KEY) {
  throw new Error("GEMINI_API_KEY no está configurado en las variables de entorno");
}

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

export const analyzeGazetteText = async (
  pagesText: Array<{ page: number; text: string }>
): Promise<AnalysisResult> => {
  const model = "gemini-2.5-pro";

  const formattedText = pagesText
    .map((p) => `--- PÁGINA ${p.page} ---\n${p.text}\n--- FIN PÁGINA ${p.page} ---`)
    .join("\n\n");

  const systemInstruction = `
    Eres un analista legal experto especializado en la legislación peruana. Tu tarea es analizar el texto del diario oficial "El Peruano" que te proporcionaré. El texto está estructurado por páginas.

    Debes realizar tres tareas principales:
    1.  Identificar la fecha de publicación principal del cuadernillo y ponerla en el campo 'gazetteDate'.
    2.  Extraer todas las normas legales (Resoluciones Ministeriales, Decretos Supremos, Leyes, etc.).
    3.  Identificar todos los movimientos de cargos públicos y clasificarlos en dos listas separadas: designados (nuevos nombramientos) y concluidos (renuncias aceptadas, ceses).

    Para cada norma legal extraída, proporciona la siguiente información:
    -   **sector**: El ministerio o sector gubernamental que emite la norma.
    -   **normId**: El identificador único de la norma.
    -   **title**: El título o sumilla de la norma.
    -   **publicationDate**: La fecha de publicación de la norma.
    -   **summary**: Un resumen conciso del propósito de la norma.
    -   **relevanceToWaterSector**: Clasifica la relevancia de la norma para el sector "Agua y Saneamiento" ('Alta', 'Media', 'Baja', 'Ninguna').
    -   **pageNumber**: El número de la página del PDF donde se encuentra la norma, basado en los marcadores "--- PÁGINA X ---".

    Para cada movimiento de cargo público, tanto designado como concluido, proporciona:
    -   **institution**: La institución o entidad gubernamental (ej. Ministerio de Defensa, COFOPRI, PROINVERSION).
    -   **personName**: El nombre completo de la persona.
    -   **position**: El cargo o posición afectado.
    -   **summary**: Un resumen breve de la acción.

    Analiza el siguiente texto y devuelve los resultados en el formato JSON especificado.
  `;

  const result = await ai.models.generateContent({
    model,
    contents: `Aquí está el texto del diario: ${formattedText}`,
    config: {
      systemInstruction,
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          gazetteDate: {
            type: Type.STRING,
            description:
              "La fecha de publicación principal del cuadernillo (ej. 'Lunes, 20 de mayo de 2024').",
          },
          norms: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                sector: { type: Type.STRING },
                normId: { type: Type.STRING },
                title: { type: Type.STRING },
                publicationDate: { type: Type.STRING },
                summary: { type: Type.STRING },
                relevanceToWaterSector: {
                  type: Type.STRING,
                  enum: [
                    Relevance.ALTA,
                    Relevance.MEDIA,
                    Relevance.BAJA,
                    Relevance.NINGUNA,
                  ],
                },
                pageNumber: { type: Type.NUMBER },
              },
              required: [
                "sector",
                "normId",
                "title",
                "publicationDate",
                "summary",
                "relevanceToWaterSector",
                "pageNumber",
              ],
            },
          },
          designatedAppointments: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                institution: { type: Type.STRING },
                personName: { type: Type.STRING },
                position: { type: Type.STRING },
                summary: { type: Type.STRING },
              },
              required: ["institution", "personName", "position", "summary"],
            },
          },
          concludedAppointments: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                institution: { type: Type.STRING },
                personName: { type: Type.STRING },
                position: { type: Type.STRING },
                summary: { type: Type.STRING },
              },
              required: ["institution", "personName", "position", "summary"],
            },
          },
        },
        required: [
          "gazetteDate",
          "norms",
          "designatedAppointments",
          "concludedAppointments",
        ],
      },
    },
  });

  const jsonString = result.text;
  const parsedResult = JSON.parse(jsonString);

  // Asegurar arrays aunque vengan null
  if (!parsedResult.designatedAppointments)
    parsedResult.designatedAppointments = [];
  if (!parsedResult.concludedAppointments)
    parsedResult.concludedAppointments = [];
  if (!parsedResult.norms) parsedResult.norms = [];
  if (!parsedResult.gazetteDate)
    parsedResult.gazetteDate = "Fecha no encontrada";

  return parsedResult as AnalysisResult;
};

// ----------------------------
// 3. Generar PDF con colores institucionales
// ----------------------------
function generateReportPdf(
  analysis: AnalysisResult,
  outputPath: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margin: 50 });
    const stream = fs.createWriteStream(outputPath);
    doc.pipe(stream);

    // Paleta institucional (puedes ajustar a tus colores exactos)
    const primaryBlue = "#0055A5"; // azul SUNASS
    const lightBlue = "#E6F0FA";
    const accentGreen = "#00A65A";

    // Encabezado
    doc.rect(0, 0, doc.page.width, 70).fill(primaryBlue);
    doc
      .fillColor("white")
      .fontSize(18)
      .font("Helvetica-Bold")
      .text("SUNASS - CION", 50, 20);
    doc
      .fontSize(12)
      .text("Análisis del Diario Oficial El Peruano", 50, 42);

    doc.moveDown(2);

    // Caja de fecha
    doc
      .fillColor(primaryBlue)
      .fontSize(14)
      .font("Helvetica-Bold")
      .text("Fecha del cuadernillo:", { continued: true });
    doc
      .fillColor("black")
      .font("Helvetica")
      .text(` ${analysis.gazetteDate}`);

    doc.moveDown();

    // Bloque Normas
    doc.rect(50, doc.y, doc.page.width - 100, 24).fill(lightBlue);
    doc
      .fillColor(primaryBlue)
      .font("Helvetica-Bold")
      .fontSize(13)
      .text("NORMAS LEGALES RELEVANTES", 60, doc.y - 18);

    doc.moveDown(2).fillColor("black").font("Helvetica").fontSize(11);

    if (analysis.norms.length === 0) {
      doc.text("No se encontraron normas en el cuadernillo.");
    } else {
      analysis.norms.forEach((n, idx) => {
        doc
          .fillColor(accentGreen)
          .font("Helvetica-Bold")
          .text(`Norma ${idx + 1}: ${n.normId}`, { continued: false });

        doc
          .fillColor(primaryBlue)
          .fontSize(11)
          .text(`Sector: ${n.sector} | Página: ${n.pageNumber}`);

        doc
          .fillColor("black")
          .font("Helvetica-Bold")
          .text(n.title);

        doc
          .font("Helvetica")
          .fontSize(10)
          .text(`Fecha de publicación: ${n.publicationDate}`);

        doc
          .font("Helvetica")
          .fontSize(10)
          .text(`Resumen: ${n.summary}`);

        doc.moveDown();

        // Salto de página suave
        if (doc.y > doc.page.height - 120) {
          doc.addPage();
        }
      });
    }

    // Nueva sección: Designaciones
    doc.addPage();
    doc.rect(50, 80, doc.page.width - 100, 24).fill(lightBlue);
    doc
      .fillColor(primaryBlue)
      .font("Helvetica-Bold")
      .fontSize(13)
      .text("DESIGNACIONES", 60, 86);

    doc.moveDown(3).fillColor("black").font("Helvetica").fontSize(11);

    if (analysis.designatedAppointments.length === 0) {
      doc.text("No se encontraron designaciones.");
    } else {
      analysis.designatedAppointments.forEach((a, idx) => {
        doc
          .fillColor(accentGreen)
          .font("Helvetica-Bold")
          .text(`Designación ${idx + 1}: ${a.personName}`);

        doc
          .fillColor(primaryBlue)
          .fontSize(10)
          .text(a.institution);

        doc
          .fillColor("black")
          .fontSize(10)
          .text(`Cargo: ${a.position}`);

        doc.text(`Resumen: ${a.summary}`);
        doc.moveDown();

        if (doc.y > doc.page.height - 120) {
          doc.addPage();
        }
      });
    }

    // Sección: Conclusiones de cargos
    doc.addPage();
    doc.rect(50, 80, doc.page.width - 100, 24).fill(lightBlue);
    doc
      .fillColor(primaryBlue)
      .font("Helvetica-Bold")
      .fontSize(13)
      .text("CONCLUSIONES / RENUNCIAS", 60, 86);

    doc.moveDown(3).fillColor("black").font("Helvetica").fontSize(11);

    if (analysis.concludedAppointments.length === 0) {
      doc.text("No se encontraron conclusiones de cargos.");
    } else {
      analysis.concludedAppointments.forEach((a, idx) => {
        doc
          .fillColor(accentGreen)
          .font("Helvetica-Bold")
          .text(`Conclusión ${idx + 1}: ${a.personName}`);

        doc
          .fillColor(primaryBlue)
          .fontSize(10)
          .text(a.institution);

        doc
          .fillColor("black")
          .fontSize(10)
          .text(`Cargo: ${a.position}`);

        doc.text(`Resumen: ${a.summary}`);
        doc.moveDown();

        if (doc.y > doc.page.height - 120) {
          doc.addPage();
        }
      });
    }

    doc.end();

    stream.on("finish", () => resolve());
    stream.on("error", (err) => reject(err));
  });
}

// ----------------------------
// 4. Main
// ----------------------------
async function main() {
  // Asumimos que el scraper deja el PDF en carpeta "downloads" y solo hay uno
  const downloadsDir = path.join(process.cwd(), "downloads");
  const files = fs.existsSync(downloadsDir)
    ? fs.readdirSync(downloadsDir).filter((f) => f.toLowerCase().endsWith(".pdf"))
    : [];

  if (files.length === 0) {
    throw new Error(
      `No se encontró ningún PDF en la carpeta ${downloadsDir}. Asegúrate de que el scraper deje allí el archivo.`
    );
  }

  const pdfPath = path.join(downloadsDir, files[0]);
  console.log(`Usando PDF para análisis: ${pdfPath}`);

  const pagesText = await extractPagesText(pdfPath);
  const analysis = await analyzeGazetteText(pagesText);

  const resultsDir = path.join(process.cwd(), "results");
  if (!fs.existsSync(resultsDir)) fs.mkdirSync(resultsDir);

  const outputName = `analisis-${analysis.gazetteDate.replace(/[^0-9A-Za-záéíóúÁÉÍÓÚñÑ]+/g, "-")}.pdf`;
  const outputPath = path.join(resultsDir, outputName);

  await generateReportPdf(analysis, outputPath);

  console.log(`✅ Informe generado en: ${outputPath}`);
}

main().catch((err) => {
  console.error("Error en analyze.ts:", err);
  process.exit(1);
});
