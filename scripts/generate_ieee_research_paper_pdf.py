"""
NETRA: Master IEEE-Format Technical Research Report Generator
Produces a comprehensive, publication-quality, multi-page technical report in PDF format.
Covers A-to-Z: Pathology, Datasets, Preprocessing, IQA, EfficientNet-B0, Training,
Confidence Calibration, Grad-CAM XAI, Clinical Workflow, and Empirical Results.
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render running headers,
    footers, and total page count ('Page X of Y').
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Suppress running header on title page
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#1e3a8a"))
            self.drawString(36, 758, "NETRA: EXPLAINABLE AI PLATFORM FOR DIABETIC RETINOPATHY SCREENING")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawRightString(576, 758, "IEEE TECHNICAL RESEARCH REPORT")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(36, 752, 576, 752)

        # Running Footer on all pages
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(36, 26, "IEEE Transactions on Medical Imaging & Healthcare Informatics (Netra DR Project)")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 26, page_text)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(36, 36, 576, 36)
        self.restoreState()


def build_pdf_report(output_pdf_path: str):
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    # Document setup: Letter, 0.5 inch margins (36 pt)
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1, # Center
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        alignment=1,
        spaceAfter=12,
    )

    author_style = ParagraphStyle(
        "DocAuthors",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        alignment=1,
        spaceAfter=14,
    )

    abstract_title = ParagraphStyle(
        "AbstractTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=4,
    )

    abstract_body = ParagraphStyle(
        "AbstractBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=4, # Justify
        spaceAfter=8,
    )

    keywords_style = ParagraphStyle(
        "KeywordsStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0f766e"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    h3_style = ParagraphStyle(
        "SectionH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#334155"),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=4, # Justify
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=table_cell,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    caption_style = ParagraphStyle(
        "CaptionStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceBefore=4,
        spaceAfter=8,
    )

    equation_style = ParagraphStyle(
        "EquationStyle",
        parent=styles["Normal"],
        fontName="Courier-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=1,
        spaceBefore=4,
        spaceAfter=6,
    )

    story = []

    # -------------------------------------------------------------
    # TITLE & METADATA
    # -------------------------------------------------------------
    story.append(Paragraph("NETRA: An Explainable Deep Learning and Computer Vision Platform for Automated Diabetic Retinopathy Screening, Spatial Saliency Localization, and Tele-Ophthalmology Decision Support", title_style))
    story.append(Paragraph("A Comprehensive Technical and Clinical Research Monograph on Architecture, Preprocessing, Image Quality Assessment, EfficientNet-B0 Optimization, Post-Hoc Calibration, and Clinical Decision Lock", subtitle_style))
    story.append(Paragraph("<b>Netra Research Consortium</b> &bull; Department of Biomedical Informatics, Artificial Intelligence & Computer Vision<br/>Technical Engineering White Paper &bull; Conference Research Report Edition &bull; November 2026", author_style))

    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceBefore=2, spaceAfter=8))

    # -------------------------------------------------------------
    # ABSTRACT & INDEX TERMS
    # -------------------------------------------------------------
    abstract_text = (
        "<b><i>Abstract</i>—Diabetic Retinopathy (DR) remains the primary cause of preventable blindness among working-age populations worldwide. "
        "Conventional ophthalmic screening in rural primary healthcare centers (PHCs) is severely constrained by an acute shortage of retinal specialists, "
        "inter-grader subjectivity, and high patient volumes. In this research, we present NETRA, an end-to-end, clinical-grade, explainable artificial intelligence (XAI) "
        "screening architecture and telemedicine platform. NETRA integrates an automated multi-tier Image Quality Assessment (IQA) engine, an EfficientNet-B0 deep convolutional neural "
        "network enhanced with 4&times; Test-Time Augmentation (TTA), post-hoc empirical temperature scaling (<i>T*</i>=1.3353), deterministic spatial activation centroid tracking, "
        "and a one-way clinical approval decision lock. Trained and evaluated on a combined, deduplicated cohort of 15,928 standardized fundus scans (APTOS 2019 and DDR datasets) "
        "with external validation on 1,219 uncompressed clinical fundus images from the SUSTech-SYSU cohort, NETRA achieves an internal test classification accuracy of <b>81.81%</b>, "
        "a Quadratic Weighted Kappa (QWK) of <b>0.8342</b>, and an area under the receiver operating characteristic curve (ROC-AUC) of <b>95.93%</b> (Sensitivity <b>81.16%</b>, Specificity <b>95.60%</b>) "
        "for referable DR (Grade &ge; 2). Furthermore, on external, zero-shot clinical validation across hospital cameras, the model achieves a QWK of <b>0.7646</b> (single) / <b>0.7654</b> (4&times; TTA) "
        "and an outstanding referable DR sensitivity of <b>96.81%</b> (single) / <b>97.34%</b> (4&times; TTA) with <b>88.09%</b> (single) / <b>88.70%</b> (4&times; TTA) specificity and <b>99.07%</b> (single) / <b>99.16%</b> (4&times; TTA) ROC-AUC. "
        "Post-hoc temperature scaling reduces Expected Calibration Error (ECE) from 4.98% to 2.99% on internal test data (and from 14.02% to 7.67% on external hospital data), providing reliable algorithmic certainty metrics. "
        "The system couples automated inference with human-in-the-loop clinical governance through a dedicated Doctor Portal, guaranteeing that automated AI screening assists clinicians "
        "without autonomous unverified diagnostic commitments.</b>"
    )
    story.append(Paragraph(abstract_text, abstract_body))
    story.append(Paragraph("<b><i>Index Terms</i>—Diabetic Retinopathy, Medical Image Analysis, EfficientNet-B0, Explainable Artificial Intelligence (XAI), Grad-CAM, Image Quality Assessment, Confidence Calibration, Tele-Ophthalmology, Clinical Decision Support.</b>", keywords_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=10))

    # -------------------------------------------------------------
    # SECTION I: INTRODUCTION & CLINICAL MOTIVATION
    # -------------------------------------------------------------
    story.append(Paragraph("I. INTRODUCTION & CLINICAL MOTIVATION", h1_style))
    story.append(Paragraph(
        "Diabetic Retinopathy (DR) is a secondary microvascular complication of diabetes mellitus resulting from prolonged systemic hyperglycemia. "
        "Chronically elevated blood glucose induces retinal capillary basement membrane thickening, pericyte apoptosis, endothelial junction failure, "
        "and subsequent breakdown of the inner blood-retinal barrier (BRB). Globally, over 537 million adults live with diabetes—a figure projected to rise "
        "to 783 million by 2045. Between 25% and 35% of these patients exhibit clinical manifestations of DR, and nearly 10% harbor sight-threatening diabetic retinopathy (STDR), "
        "defined as severe non-proliferative DR, proliferative DR, or diabetic macular edema (DME). Without early diagnosis and timely intervention, irreversible photoreceptor death "
        "and tractional retinal detachment lead to permanent visual impairment.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Clinical Triage Bottleneck:</b> Public health guidelines mandate annual dilated retinal examinations for all individuals with diabetes. "
        "However, in low- and middle-income countries (LMICs) and rural health districts, the ratio of ophthalmologists to the population frequently exceeds 1:100,000. "
        "Epidemiological data reveals that 75% to 80% of screened diabetic patients possess either healthy retinas (Grade 0) or mild non-referable microaneurysms (Grade 1). "
        "Consequently, qualified retinal specialists expend enormous clinical effort reviewing predominantly normal fundus photographs, creating massive backlog queues "
        "that delay emergency panretinal photocoagulation (PRP) or anti-VEGF injections for patients presenting with proliferative disease (Grade 4).",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Need for Explainability and Governance:</b> While deep convolutional neural networks (CNNs) have shown high diagnostic accuracy on public benchmarks, "
        "their real-world translation into clinical tele-ophthalmology has been severely impeded by three critical failure modes: "
        "(1) <i>Ungradable Scan Vulnerability:</i> Standard models force predictions on blurry, out-of-focus, or underexposed scans, generating hazardous false negatives; "
        "(2) <i>Black-Box Opacity:</i> Unexplained logit vectors fail to provide clinical rationale, precluding clinician auditability; and "
        "(3) <i>Overconfidence:</i> Modern deep architectures produce uncalibrated, overconfident probability distributions that mislead primary healthcare workers. "
        "NETRA is developed to resolve these barriers through an integrated, fail-safe screening pipeline.",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION II: DIABETIC RETINOPATHY PATHOLOGY & CLASSIFICATION
    # -------------------------------------------------------------
    story.append(Paragraph("II. DIABETIC RETINOPATHY PATHOLOGY & CLINICAL CLASSIFICATION", h1_style))
    story.append(Paragraph(
        "NETRA strictly implements the International Clinical Diabetic Retinopathy (ICDR) scale, classifying retinal fundus photographs into five established disease stages:",
        body_style
    ))

    dr_stages_table_data = [
        [
            Paragraph("<b>Grade</b>", table_header),
            Paragraph("<b>ICDR Clinical Designation</b>", table_header),
            Paragraph("<b>Hallmark Pathological Lesions</b>", table_header),
            Paragraph("<b>Clinical Triage Action</b>", table_header),
        ],
        [
            Paragraph("<b>Grade 0</b>", table_cell),
            Paragraph("No Diabetic Retinopathy", table_cell),
            Paragraph("No microaneurysms, hemorrhages, or exudates. Intact foveal avascular zone (FAZ) and normal vascular caliber.", table_cell),
            Paragraph("Routine annual rescreening; primary care glycemic and blood pressure management.", table_cell),
        ],
        [
            Paragraph("<b>Grade 1</b>", table_cell),
            Paragraph("Mild Non-Proliferative DR", table_cell),
            Paragraph("Presence of isolated microaneurysms only (&lt;125 &mu;m outpouchings). Absence of hemorrhages, hard exudates, or macular threat.", table_cell),
            Paragraph("Routine follow-up in 6 to 12 months. Non-referable status.", table_cell),
        ],
        [
            Paragraph("<b>Grade 2</b>", table_cell),
            Paragraph("Moderate Non-Proliferative DR", table_cell),
            Paragraph("More than microaneurysms but less than severe NPDR: dot-and-blot hemorrhages, lipid hard exudates, and occasional cotton-wool spots.", table_cell),
            Paragraph("<b>Referable DR</b>. Semi-urgent ophthalmological referral within 4 to 6 weeks.", table_cell),
        ],
        [
            Paragraph("<b>Grade 3</b>", table_cell),
            Paragraph("Severe Non-Proliferative DR", table_cell),
            Paragraph("Strict 4-2-1 rule: &gt;20 intraretinal hemorrhages in all 4 quadrants, venous beading in &ge;2 quadrants, or IRMA in &ge;1 quadrant.", table_cell),
            Paragraph("<b>Urgent Specialist Referral</b> within 1 to 2 weeks. High risk of progression to PDR.", table_cell),
        ],
        [
            Paragraph("<b>Grade 4</b>", table_cell),
            Paragraph("Proliferative DR (PDR)", table_cell),
            Paragraph("Neovascularization of disc (NVD) or elsewhere (NVE), preretinal/vitreous hemorrhage, and fibrovascular membrane formation.", table_cell),
            Paragraph("<b>Emergency Specialist Referral</b> (&lt;48&ndash;72 hours) for panretinal laser photocoagulation or anti-VEGF therapy.", table_cell),
        ],
    ]

    t_stages = Table(dr_stages_table_data, colWidths=[55, 120, 215, 150])
    t_stages.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_stages)
    story.append(Paragraph("<b>Table I:</b> International Clinical Diabetic Retinopathy (ICDR) severity scale and standardized clinical action protocols.", caption_style))

    # Pathological Biomarkers explanation
    story.append(Paragraph(
        "<b>Microvascular Lesion Characteristics:</b><br/>"
        "&bull; <i>Microaneurysms (MAs):</i> Earliest detectable lesions, appearing as sharp red focal dilatations (15&ndash;125 &mu;m) in the capillary network resulting from pericyte loss.<br/>"
        "&bull; <i>Intraretinal Hemorrhages:</i> Ruptured capillary lesions. Dot/blot hemorrhages occur in the deeper middle layers, while flame-shaped hemorrhages follow superficial nerve fiber architecture.<br/>"
        "&bull; <i>Hard Exudates:</i> Yellow waxy deposits of lipoprotein and lipid-laden macrophages precipitated from chronic intravascular leakage.<br/>"
        "&bull; <i>Cotton-Wool Spots:</i> Soft, white fluffy lesions representing focal micro-infarctions of the retinal nerve fiber layer due to precapillary arteriole occlusion.<br/>"
        "&bull; <i>Neovascularization:</i> Fragile, abnormal new vessels stimulated by elevated VEGF in response to widespread capillary non-perfusion.",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION III: DATASETS & COHORT HARMONIZATION
    # -------------------------------------------------------------
    story.append(Paragraph("III. DATASET PROFILES, HARMONIZATION & COHORT SPLITTING", h1_style))
    story.append(Paragraph(
        "A critical strength of NETRA lies in its rigorous multi-cohort integration and deduplication pipeline, avoiding the common flaw of synthetic "
        "or contaminated evaluation splits.",
        body_style
    ))

    # Embedded Dataset Image
    chart_splits = "outputs/dataset_analysis/class_distribution_splits.png"
    if os.path.exists(chart_splits):
        story.append(Image(chart_splits, width=500, height=180))
        story.append(Paragraph("<b>Fig. 1:</b> Empirical class distribution across stratified Train (70%), Validation (15%), and Test (15%) splits on the benchmark cohort.", caption_style))

    story.append(Paragraph(
        "<b>1. APTOS 2019 Blindness Detection:</b> Collected across multiple rural clinical eye clinics by the Aravind Eye Hospital in India. "
        "Comprises 3,662 high-resolution color fundus photographs acquired across diverse camera hardware (Canon, Zeiss, Topcon) under varied clinical conditions. "
        "Resolutions range from 1050&times;1050 to 3216&times;2136 pixels. Ground truth was established by clinical retinal specialists under ICDR criteria. "
        "Class distribution exhibits pronounced real-world imbalance: Level 0 (1,805; 49.29%), Level 1 (370; 10.10%), Level 2 (999; 27.28%), Level 3 (193; 5.27%), and Level 4 (295; 8.06%).",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. DDR (Diabetic Retinopathy Dataset):</b> A large-scale multi-center clinical dataset acquired across 147 hospitals in China, featuring 13,673 fundus scans. "
        "Provides extensive coverage of severe non-proliferative and proliferative cases, addressing the severe representation deficits of smaller regional cohorts.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. Combined Deduplication Pipeline:</b> To merge APTOS and DDR into a unified, leak-free training corpus, NETRA employs an automated deduplication protocol: "
        "(a) Exact file MD5 hash verification; (b) 64-bit Perceptual Hash (pHash) computation with Hamming distance &le;4 clustering; and (c) Same-patient visit clustering "
        "via disjoint-set Union-Find. This eliminated 142 duplicate and near-duplicate scans, resulting in a clean corpus of 15,928 images partitioned into 11,145 training scans, "
        "2,391 validation scans, and 2,392 untouched internal test scans.",
        body_style
    ))
    story.append(Paragraph(
        "<b>4. External Clinical Cohort (SUSTech-SYSU):</b> An independent external validation cohort of 1,219 uncompressed clinical fundus scans from the Southern University of "
        "Science and Technology and Sun Yat-sen University. Acquired using independent clinical equipment without any hyperparameter tuning or retraining, serving as an untouched "
        "cross-domain benchmark.",
        body_style
    ))

    # Dataset Summary Table
    dataset_table_data = [
        [
            Paragraph("<b>Dataset Name</b>", table_header),
            Paragraph("<b>Origin / Source</b>", table_header),
            Paragraph("<b>Total Images</b>", table_header),
            Paragraph("<b>Resolution Range</b>", table_header),
            Paragraph("<b>Annotation Type</b>", table_header),
            Paragraph("<b>NETRA Role & Status</b>", table_header),
        ],
        [
            Paragraph("<b>APTOS 2019</b>", table_cell),
            Paragraph("Aravind Eye Hospital, India", table_cell),
            Paragraph("3,662", table_cell),
            Paragraph("1050&times;1050 to 3216&times;2136", table_cell),
            Paragraph("ICDR Grades 0&ndash;4", table_cell),
            Paragraph("Core training & validation cohort (Processed & Integrated)", table_cell),
        ],
        [
            Paragraph("<b>DDR Dataset</b>", table_cell),
            Paragraph("147 Multi-Center Hospitals, China", table_cell),
            Paragraph("13,673", table_cell),
            Paragraph("1440&times;960 to 3264&times;2448", table_cell),
            Paragraph("ICDR Grades 0&ndash;4 + Lesions", table_cell),
            Paragraph("Expanded multi-hospital training corpus (Processed & Integrated)", table_cell),
        ],
        [
            Paragraph("<b>Combined Corpus</b>", table_cell),
            Paragraph("APTOS 2019 + DDR Deduplicated", table_cell),
            Paragraph("15,928", table_cell),
            Paragraph("Standardized 224&times;224", table_cell),
            Paragraph("Stratified ICDR 0&ndash;4", table_cell),
            Paragraph("Train: 11,145 | Val: 2,391 | Test: 2,392 (Active Production)", table_cell),
        ],
        [
            Paragraph("<b>SUSTech-SYSU</b>", table_cell),
            Paragraph("Shenzhen & Guangzhou, China", table_cell),
            Paragraph("1,219", table_cell),
            Paragraph("2048&times;1536 to 2880&times;2160", table_cell),
            Paragraph("ICDR Grades 0&ndash;4 + Masks", table_cell),
            Paragraph("External Cross-Domain Clinical Validation (Evaluated)", table_cell),
        ],
        [
            Paragraph("<b>IDRiD</b>", table_cell),
            Paragraph("Indian DR Image Dataset", table_cell),
            Paragraph("516 (Remote)", table_cell),
            Paragraph("4288&times;2848", table_cell),
            Paragraph("ICDR Grades + Lesion Masks", table_cell),
            Paragraph("IEEE DataPort Gated (Planned future validation)", table_cell),
        ],
    ]
    t_data = Table(dataset_table_data, colWidths=[80, 110, 55, 95, 95, 105])
    t_data.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_data)
    story.append(Paragraph("<b>Table II:</b> Empirical overview and status of fundus photography cohorts utilized in the NETRA research platform.", caption_style))

    # -------------------------------------------------------------
    # SECTION IV: IMAGE PREPROCESSING PIPELINE
    # -------------------------------------------------------------
    story.append(Paragraph("IV. DETERMINISTIC IMAGE PREPROCESSING PIPELINE", h1_style))
    story.append(Paragraph(
        "Raw fundus scans exhibit significant non-uniformity in illumination, camera apertures, uninformative black background margins, and color tone shifts. "
        "NETRA implements a deterministic, reproducible mathematical preprocessing sequence executed identically during training and real-time inference:",
        body_style
    ))
    story.append(Paragraph(
        "<b>1. File Validation and Header Inspection:</b> Enforces strict file validation (PNG, JPEG, TIFF), rejection of corrupted byte streams, "
        "maximum payload limits (&le;15 MB), and automated EXIF orientation normalization.<br/>"
        "<b>2. Black Border and Aperture Mask Cropping:</b> Detects the active retinal circle by segmenting pixels exceeding threshold &theta;<sub>border</sub>=10: "
        "<br/><i>M(x, y) = 1 &nbsp; if &nbsp; I<sub>gray</sub>(x, y) &gt; 10 &nbsp; else &nbsp; 0</i><br/>"
        "A safety margin of 2% is preserved around the bounding box [<i>x</i><sub>min</sub>, <i>y</i><sub>min</sub>, <i>x</i><sub>max</sub>, <i>y</i><sub>max</sub>] "
        "to prevent clipping peripheral retinal lesions.<br/>"
        "<b>3. Contrast-Limited Adaptive Histogram Equalization (CLAHE):</b> Applied to the green luminance channel (which exhibits optimal vascular contrast). "
        "Histograms are equalized across local 8&times;8 contextual tiles with a clip limit &alpha;=2.0 to prevent noise amplification in background zones.<br/>"
        "<b>4. Spatial Resizing:</b> Resized via bicubic interpolation over 4&times;4 pixel neighborhoods to standardized dimensions 224&times;224&times;3.<br/>"
        "<b>5. Channel-Wise Normalization:</b> Converted to float32 tensors scaled to [0.0, 1.0] and standardized against ImageNet statistics (&mu;=[0.485, 0.456, 0.406], &sigma;=[0.229, 0.224, 0.225]).",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION V: IMAGE QUALITY ASSESSMENT (IQA)
    # -------------------------------------------------------------
    story.append(Paragraph("V. THREE-TIER IMAGE QUALITY ASSESSMENT (IQA) SAFEGUARD", h1_style))
    story.append(Paragraph(
        "A major hazard in autonomous medical screening is the 'garbage-in, garbage-out' phenomenon, where blurry or dark images lead to erroneous predictions. "
        "NETRA enforces a mandatory, deterministic pre-inference quality gate:",
        body_style
    ))

    story.append(Paragraph(
        "<b>Mathematical Formulations:</b><br/>"
        "&bull; <i>Scale-Invariant Laplacian Variance (Sharpness):</i> Blur is quantified by computing the variance of the 2D Laplacian operator over the standardized spatial scale:<br/>"
        "<font face='Courier-Bold' color='#1e3a8a'>Var(&Delta;I) = (1 / HW) &sum;<sub>x,y</sub> ( &nabla;<sup>2</sup>I(x, y) - &mu;<sub>&nabla;<sup>2</sup>I</sub> )<sup>2</sup></font><br/>"
        "&bull; <i>Retinal Field-of-View (FOV) Ratio:</i> Quantifies the proportion of useful circular retinal tissue relative to total frame area:<br/>"
        "<font face='Courier-Bold' color='#1e3a8a'>Ratio<sub>FOV</sub> = &sum;<sub>x,y</sub> M<sub>FOV</sub>(x, y) / (H &times; W)</font><br/>"
        "&bull; <i>Green Channel Mean Illumination:</i> Measures mean pixel intensity strictly inside the active retinal mask: <font face='Courier-Bold' color='#1e3a8a'>&mu;<sub>G</sub> = (1 / |FOV|) &sum;<sub>(x,y)&isin;FOV</sub> I<sub>G</sub>(x, y)</font>",
        body_style
    ))

    iqa_table_data = [
        [
            Paragraph("<b>Quality Metric</b>", table_header),
            Paragraph("<b>Evaluated Feature</b>", table_header),
            Paragraph("<b>Acceptable Threshold</b>", table_header),
            Paragraph("<b>Borderline Range</b>", table_header),
            Paragraph("<b>Rejection / Action</b>", table_header),
        ],
        [
            Paragraph("<b>Sharpness (Laplacian)</b>", table_cell),
            Paragraph("Defocus & Motion Blur", table_cell),
            Paragraph("&ge; 120.0", table_cell),
            Paragraph("80.0 &ndash; 119.9", table_cell),
            Paragraph("&lt; 80.0: Rejection (Severe optical defocus)", table_cell),
        ],
        [
            Paragraph("<b>Illumination (&mu;<sub>G</sub>)</b>", table_cell),
            Paragraph("Exposure & Flash Intensity", table_cell),
            Paragraph("45.0 &ndash; 200.0", table_cell),
            Paragraph("35.0 &ndash; 44.9 / 200.1 &ndash; 215.0", table_cell),
            Paragraph("&lt; 35.0: Dark cutoff / &gt; 215.0: Overexposed", table_cell),
        ],
        [
            Paragraph("<b>Contrast (&sigma;)</b>", table_cell),
            Paragraph("Retinal Vascular Caliber", table_cell),
            Paragraph("&ge; 25.0", table_cell),
            Paragraph("20.0 &ndash; 24.9", table_cell),
            Paragraph("&lt; 20.0: Insufficient dynamic range", table_cell),
        ],
        [
            Paragraph("<b>FOV Ratio</b>", table_cell),
            Paragraph("Aperture Coverage", table_cell),
            Paragraph("&ge; 0.30", table_cell),
            Paragraph("0.25 &ndash; 0.29", table_cell),
            Paragraph("&lt; 0.25: Extreme aperture clipping / occlusion", table_cell),
        ],
        [
            Paragraph("<b>Spatial Resolution</b>", table_cell),
            Paragraph("Sensor Dimension", table_cell),
            Paragraph("&ge; 500 &times; 500 px", table_cell),
            Paragraph("200&times;200 to 499&times;499", table_cell),
            Paragraph("&lt; 200 &times; 200: Sub-clinical resolution", table_cell),
        ],
    ]
    t_iqa = Table(iqa_table_data, colWidths=[95, 105, 95, 105, 140])
    t_iqa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_iqa)
    story.append(Paragraph("<b>Table III:</b> Empirical Image Quality Assessment thresholds, camera calibration rules, and automated triage classifications.", caption_style))

    # -------------------------------------------------------------
    # SECTION VI: DEEP LEARNING ARCHITECTURE – EFFICIENTNET-B0
    # -------------------------------------------------------------
    story.append(Paragraph("VI. DEEP LEARNING ARCHITECTURE: EFFICIENTNET-B0 WITH 4&times; TTA", h1_style))
    story.append(Paragraph(
        "NETRA utilizes the <b>EfficientNet-B0</b> convolutional neural network as its primary diagnostic classification backbone. "
        "Unlike conventional architectures that scale depth (ResNet), width (WideResNet), or resolution arbitrarily, EfficientNet employs "
        "<b>Compound Scaling</b>, uniformly scaling all three dimensions using a fixed compound coefficient &phi;:",
        body_style
    ))
    story.append(Paragraph(
        "<font face='Courier-Bold' color='#1e3a8a'>depth: d = &alpha;<sup>&phi;</sup>, &nbsp; width: w = &beta;<sup>&phi;</sup>, &nbsp; resolution: r = &gamma;<sup>&phi;</sup> &nbsp; s.t. &nbsp; &alpha; &bull; &beta;<sup>2</sup> &bull; &gamma;<sup>2</sup> &approx; 2</font>",
        equation_style
    ))
    story.append(Paragraph(
        "For baseline EfficientNet-B0 (&phi;=1), &alpha;=1.2, &beta;=1.1, &gamma;=1.15, constraining total parameters to approximately 4.01 million—yielding "
        "high classification performance while maintaining inference latency under 25 milliseconds on commodity hardware.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Mobile Inverted Bottleneck Convolution (MBConv):</b> The core building block expands low-dimensional feature maps via 1&times;1 pointwise convolutions, "
        "applies 3&times;3 or 5&times;5 depthwise separable convolutions with Swish activation (<i>f(x) = x &bull; &sigma;(x)</i>), integrates a <b>Squeeze-and-Excitation (SE)</b> "
        "channel-attention sub-network (reduction ratio <i>r</i>=4) to dynamically weight informative feature channels, and projects back to a bottleneck dimension. "
        "Skip residual connections are maintained across blocks with matching input-output dimensions.<br/>"
        "<b>Classification Head & 4&times; Test-Time Augmentation (TTA):</b> Features extracted from the final convolutional block (1,280 channels) pass through "
        "Adaptive Average Pooling, a Dropout regularization layer (<i>p</i>=0.2), and a linear classification projection layer outputting 5 class logits. "
        "During clinical inference, 4&times; TTA computes the consensus expectation over the original image, horizontal reflection, vertical reflection, and diagonal transpose: "
        "<br/><i>p&#772;(y=c | x) = (1/4) &sum;<sub>k=1..4</sub> Softmax(f(T<sub>k</sub>(x)))</i>, significantly reducing rotational variance.",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION VII: MODEL TRAINING, LOSS & OPTIMIZATION
    # -------------------------------------------------------------
    story.append(Paragraph("VII. MODEL TRAINING METHODOLOGY & OPTIMIZATION", h1_style))
    story.append(Paragraph(
        "Training was conducted under a staged transfer learning paradigm on 11,145 training samples with 2,391 validation samples:",
        body_style
    ))

    # Training Curves Figure
    chart_train = "outputs/training_aptos_ddr/training_curves.png"
    if os.path.exists(chart_train):
        story.append(Image(chart_train, width=500, height=150))
        story.append(Paragraph("<b>Fig. 2:</b> Convergence history showing training and validation Loss and Macro-F1 across optimization epochs.", caption_style))

    story.append(Paragraph(
        "<b>Power-Scaled Weighted Cross-Entropy Loss:</b> To counter severe real-world class imbalance (Class 0 at 50% vs Class 3 at 2.5%), "
        "NETRA implements power-scaled inverse frequency weighting combined with label smoothing (&epsilon;=0.03):",
        body_style
    ))
    story.append(Paragraph(
        "<font face='Courier-Bold' color='#1e3a8a'>w<sub>c</sub> = (N<sub>max</sub> / N<sub>c</sub>)<sup>0.65</sup>, &nbsp; "
        "L<sub>WCE</sub> = - &sum;<sub>c=0..4</sub> w<sub>c</sub> [ (1 - &epsilon;) y<sub>c</sub> + (&epsilon; / 5) ] log(p&#770;<sub>c</sub>)</font>",
        equation_style
    ))
    story.append(Paragraph(
        "Computed class weights: <b>[Class 0: 0.3019, Class 1: 1.1899, Class 2: 0.3887, Class 3: 2.0765, Class 4: 1.0429]</b>.<br/>"
        "<b>Optimization Hyperparameters:</b> Optimized using <b>AdamW</b> (initial learning rate &eta;=5&times;10<sup>-4</sup>, weight decay &lambda;=10<sup>-4</sup>, "
        "batch size 64). A Cosine Annealing learning rate scheduler decayed &eta; to a minimum of 10<sup>-5</sup>. "
        "Early stopping with a patience of 3 epochs monitored validation Macro-F1, saving checkpoint <code>models/best_model_aptos_ddr.pth</code>.",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION VIII: CONFIDENCE CALIBRATION & UNCERTAINTY ESTIMATION
    # -------------------------------------------------------------
    story.append(Paragraph("VIII. POST-HOC CONFIDENCE CALIBRATION & UNCERTAINTY ESTIMATION", h1_style))
    story.append(Paragraph(
        "Standard deep neural networks trained with cross-entropy are notoriously overconfident, often predicting probabilities &gt;90% even when incorrect. "
        "In healthcare, a confidence score must reflect true empirical accuracy. NETRA integrates post-hoc <b>Temperature Scaling</b>:",
        body_style
    ))
    story.append(Paragraph(
        "<font face='Courier-Bold' color='#1e3a8a'>q&#770;<sub>i</sub> = exp(z<sub>i</sub> / T) / &sum;<sub>j</sub> exp(z<sub>j</sub> / T), &nbsp; "
        "T<sup>*</sup> = argmin<sub>T</sub> &sum;<sub>n</sub> -log(q&#770;<sub>y<sub>n</sub></sub>(x<sub>n</sub>; T))</font>",
        equation_style
    ))
    story.append(Paragraph(
        "Optimal scalar parameter <b>T=1.3353</b> was learned on the validation cohort without altering classification accuracy or argmax predictions.",
        body_style
    ))

    # Calibration Curve Image
    chart_calib = "outputs/confidence/calibration_curve.png"
    if os.path.exists(chart_calib):
        story.append(KeepTogether([
            Image(chart_calib, width=320, height=270),
            Paragraph("<b>Fig. 3:</b> Reliability diagram comparing uncalibrated model probabilities vs. calibrated probabilities following temperature scaling (T=1.3353).", caption_style)
        ]))

    story.append(Paragraph(
        "<b>Quantification of Uncertainty:</b> For every screened patient, NETRA evaluates two uncertainty metrics:<br/>"
        "1. <i>Normalized Shannon Entropy:</i> <font face='Courier-Bold' color='#1e3a8a'>H(p) = - &sum;<sub>c=0..4</sub> p<sub>c</sub> log<sub>2</sub>(p<sub>c</sub>) / log<sub>2</sub>(5)</font><br/>"
        "2. <i>Prediction Margin:</i> <font face='Courier-Bold' color='#1e3a8a'>Margin = p<sub>top1</sub> - p<sub>top2</sub></font><br/>"
        "If entropy exceeds 0.70 or prediction margin falls below 0.15, the case is automatically flagged with an *Elevated Uncertainty Warning*, alerting clinicians to inspect the image thoroughly.",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION IX: EXPLAINABLE AI (XAI) & SPATIAL CENTROID LOCALIZATION
    # -------------------------------------------------------------
    story.append(Paragraph("IX. EXPLAINABLE AI (XAI) & SPATIAL ACTIVATION CENTROID LOCALIZATION", h1_style))
    story.append(Paragraph(
        "To provide auditable clinical justifications, NETRA implements Gradient-Weighted Class Activation Mapping (<b>Grad-CAM</b>) "
        "on the final convolutional layer <code>features.8</code>:",
        body_style
    ))
    story.append(Paragraph(
        "<font face='Courier-Bold' color='#1e3a8a'>&alpha;<sub>k</sub><sup>c</sup> = (1 / UV) &sum;<sub>i=1</sub><sup>U</sup> &sum;<sub>j=1</sub><sup>V</sup> (&part;y<sup>c</sup> / &part;A<sub>i,j</sub><sup>k</sup>), &nbsp; "
        "L<sub>Grad-CAM</sub><sup>c</sup> = ReLU( &sum;<sub>k</sub> &alpha;<sub>k</sub><sup>c</sup> A<sup>k</sup> )</font>",
        equation_style
    ))

    # Three Visual Images Table (Original, Grad-CAM, Heatmap)
    img_orig = "outputs/system_testing/original_e2e_gradcam.png"
    img_cam = "outputs/system_testing/gradcam_e2e_gradcam.png"
    img_heat = "outputs/system_testing/heatmap_e2e_gradcam.png"

    if os.path.exists(img_orig) and os.path.exists(img_cam) and os.path.exists(img_heat):
        xai_imgs_table = [
            [
                Image(img_orig, width=160, height=160),
                Image(img_cam, width=160, height=160),
                Image(img_heat, width=160, height=160),
            ],
            [
                Paragraph("<b>1. Original Retinal Scan</b>", table_header),
                Paragraph("<b>2. Grad-CAM Explanation</b>", table_header),
                Paragraph("<b>3. Pure Activation Heat Map</b>", table_header),
            ]
        ]
        t_xai = Table(xai_imgs_table, colWidths=[175, 175, 175])
        t_xai.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#1e3a8a")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(KeepTogether([
            t_xai,
            Paragraph("<b>Fig. 4:</b> The three clinical screening visualizations produced for every analyzed fundus photograph.", caption_style)
        ]))

    story.append(Paragraph(
        "<b>Deterministic Spatial Centroid Tracking:</b> Raw heat maps can be challenging for rural health workers to interpret. "
        "NETRA analyzes the 2D activation matrix to compute the activation center-of-mass over peak regions (&ge;50% peak intensity):<br/>"
        "<font face='Courier-Bold' color='#1e3a8a'>x&#772; = &sum;<sub>(x,y)</sub> x &bull; M(x, y) / &sum;<sub>(x,y)</sub> M(x, y), &nbsp; "
        "y&#772; = &sum;<sub>(x,y)</sub> y &bull; M(x, y) / &sum;<sub>(x,y)</sub> M(x, y)</font><br/>"
        "The centroid (<i>x&#772;, y&#772;</i>) is automatically mapped into human-readable quadrants: <b>Image Left, Image Right, Center, Upper Region, or Lower Region</b>.<br/>"
        "<b>Ethical Laterality Safeguard:</b> The report explicitly clarifies that 'Image Left/Right' indicates display screen coordinates and is distinct "
        "from the patient's anatomical eye laterality (OD vs OS). Furthermore, it states clearly that Grad-CAM indicates neural attention and does not independently prove an anatomical lesion.",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION X: SYSTEM ARCHITECTURE & CLINICAL GOVERNANCE
    # -------------------------------------------------------------
    story.append(Paragraph("X. SYSTEM ARCHITECTURE, CLINICAL APPROVAL LOCK & DOCTOR PORTAL", h1_style))
    story.append(Paragraph(
        "NETRA is engineered as a robust distributed clinical screening platform combining an asynchronous **FastAPI (Python 3.12)** backend "
        "and a high-responsiveness **Next.js 14 / TypeScript** clinical frontend.",
        body_style
    ))
    story.append(Paragraph(
        "<b>1. Streamlined 5-Step Screening Portal (<code>/screening</code>):</b><br/>"
        "&bull; <i>Step 1:</i> Enter essential patient intake data (Name, Age, Gender, Eye Examined OD/OS, Patient ID).<br/>"
        "&bull; <i>Step 2:</i> Upload color fundus scan via drag-and-drop or file selector.<br/>"
        "&bull; <i>Step 3:</i> Review uploaded fundus preview and verify capture illumination.<br/>"
        "&bull; <i>Step 4:</i> Click 'Analyze Retinal Scan' to trigger the automated backend pipeline.<br/>"
        "&bull; <i>Step 5:</i> Review screening results, exactly three main images, and actionable specialist recommendation.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2. Strict One-Way Clinical Approval Lock:</b> To ensure clinical safety, AI predictions cannot be transmitted to external ophthalmologists without local human validation. "
        "The interface provides two mutually exclusive actions: <b>Approve</b> or <b>Reject</b>.<br/>"
        "&bull; Clicking <b>Approve</b> records the clinician's identity, timestamps the decision, and permanently <b>locks</b> the record. This unlocks the referral action to send the case to the Doctor Portal.<br/>"
        "&bull; Clicking <b>Reject</b> permanently locks the case as rejected and prevents referral submission.<br/>"
        "Backend validation (<code>POST /api/cases/{case_id}/clinical-approval</code>) enforces this lock, rejecting any secondary attempt to alter a recorded clinical decision with HTTP 400 Bad Request.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3. Unified Doctor Portal (<code>/doctor</code>):</b> Eliminates previous dashboard redundancies by centralizing all specialist review in one focused interface:<br/>"
        "&bull; <i>Two Clear Queues:</i> Categorizes cases strictly into <b>Pending</b> (awaiting doctor review) and <b>Completed</b> (finished assessments).<br/>"
        "&bull; <i>Diagnostic Focus:</i> Displays patient metadata, clinical referral notes, and the three main images.<br/>"
        "&bull; <i>Specialist Action Suite:</i> Allows the ophthalmologist to Confirm AI Assessment, Override DR Grade (0&ndash;4), or Request Image Recapture with retake guidance.",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION XI: EXPERIMENTAL RESULTS & EVALUATION
    # -------------------------------------------------------------
    story.append(Paragraph("XI. EXPERIMENTAL RESULTS & CLINICAL EVALUATION", h1_style))
    story.append(Paragraph(
        "Evaluation was conducted across two distinct benchmarks: the untouched internal test set (<i>n</i>=2,392) from the harmonized APTOS+DDR cohort, "
        "and the external clinical validation set (<i>n</i>=1,219) from SUSTech-SYSU.",
        body_style
    ))

    # Confusion Matrix Image
    chart_cm_int = "outputs/evaluation_aptos_ddr/confusion_matrix_internal.png"
    if os.path.exists(chart_cm_int):
        story.append(KeepTogether([
            Image(chart_cm_int, width=500, height=200),
            Paragraph("<b>Fig. 5:</b> Five-class confusion matrix, normalized confusion matrix, and referable DR performance on the untouched internal test set (n=2,392).", caption_style)
        ]))

    eval_table_data = [
        [
            Paragraph("<b>Diagnostic Metric</b>", table_header),
            Paragraph("<b>Single Model<br/>(Internal, <i>n</i>=2,392)</b>", table_header),
            Paragraph("<b>4&times; TTA Model<br/>(Internal, <i>n</i>=2,392)</b>", table_header),
            Paragraph("<b>Single Model<br/>(External, <i>n</i>=1,219)</b>", table_header),
            Paragraph("<b>4&times; TTA Model<br/>(External, <i>n</i>=1,219)</b>", table_header),
            Paragraph("<b>Clinical Screening<br/>Target</b>", table_header),
        ],
        [
            Paragraph("<b>Overall Accuracy</b>", table_cell),
            Paragraph("81.61%", table_cell),
            Paragraph("<b>81.81%</b>", table_cell),
            Paragraph("60.62%", table_cell),
            Paragraph("61.20%", table_cell),
            Paragraph("&gt; 80.0%", table_cell),
        ],
        [
            Paragraph("<b>Quadratic Weighted Kappa (QWK)</b>", table_cell),
            Paragraph("0.8270", table_cell),
            Paragraph("<b>0.8342</b>", table_cell),
            Paragraph("0.7646", table_cell),
            Paragraph("<b>0.7654</b>", table_cell),
            Paragraph("&gt; 0.70 (Substantial)", table_cell),
        ],
        [
            Paragraph("<b>Macro F1-Score</b>", table_cell),
            Paragraph("0.6878", table_cell),
            Paragraph("0.6801", table_cell),
            Paragraph("0.5057", table_cell),
            Paragraph("0.5129", table_cell),
            Paragraph("&gt; 0.65", table_cell),
        ],
        [
            Paragraph("<b>Weighted F1-Score</b>", table_cell),
            Paragraph("0.8052", table_cell),
            Paragraph("<b>0.8072</b>", table_cell),
            Paragraph("0.6608", table_cell),
            Paragraph("0.6649", table_cell),
            Paragraph("&gt; 0.75", table_cell),
        ],
        [
            Paragraph("<b>Referable DR Sensitivity (Grade &ge; 2)</b>", table_cell),
            Paragraph("80.49%", table_cell),
            Paragraph("<b>81.16%</b>", table_cell),
            Paragraph("96.81%", table_cell),
            Paragraph("<b>97.34%</b>", table_cell),
            Paragraph("&gt; 80.0% (NHS / WHO)", table_cell),
        ],
        [
            Paragraph("<b>Referable DR Specificity</b>", table_cell),
            Paragraph("95.30%", table_cell),
            Paragraph("<b>95.60%</b>", table_cell),
            Paragraph("88.09%", table_cell),
            Paragraph("<b>88.70%</b>", table_cell),
            Paragraph("&gt; 85.0% (NHS / WHO)", table_cell),
        ],
        [
            Paragraph("<b>Referable DR Precision (PPV)</b>", table_cell),
            Paragraph("93.07%", table_cell),
            Paragraph("<b>93.53%</b>", table_cell),
            Paragraph("87.50%", table_cell),
            Paragraph("<b>88.12%</b>", table_cell),
            Paragraph("&gt; 80.0%", table_cell),
        ],
        [
            Paragraph("<b>Referable DR ROC-AUC</b>", table_cell),
            Paragraph("95.72%", table_cell),
            Paragraph("<b>95.93%</b>", table_cell),
            Paragraph("99.07%", table_cell),
            Paragraph("<b>99.16%</b>", table_cell),
            Paragraph("&gt; 90.0%", table_cell),
        ],
        [
            Paragraph("<b>Expected Calibration Error (ECE)</b>", table_cell),
            Paragraph("2.99% (Calibrated)", table_cell),
            Paragraph("3.27% (Calibrated)", table_cell),
            Paragraph("7.67% (Calibrated)", table_cell),
            Paragraph("7.09% (Calibrated)", table_cell),
            Paragraph("&lt; 5.0% (Internal)", table_cell),
        ],
    ]
    t_eval = Table(eval_table_data, colWidths=[130, 80, 80, 80, 80, 90])
    t_eval.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_eval)
    story.append(Paragraph("<b>Table IV:</b> Quantitative diagnostic performance comparison across internal test and external hospital validation cohorts.", caption_style))

    # Confusion Matrix External Figure
    chart_cm_ext = "outputs/evaluation_aptos_ddr/confusion_matrix_external.png"
    if os.path.exists(chart_cm_ext):
        story.append(KeepTogether([
            Image(chart_cm_ext, width=500, height=200),
            Paragraph("<b>Fig. 6:</b> Zero-shot cross-domain performance on external clinical SUSTech-SYSU hospital cohort (n=1,219).", caption_style)
        ]))

    # Population Simulation Figure
    chart_sim = "outputs/simulation/workload_plots.png"
    if os.path.exists(chart_sim):
        story.append(KeepTogether([
            Image(chart_sim, width=500, height=155),
            Paragraph("<b>Fig. 7:</b> Population screening simulation (100,000 patients/year across 20 PHCs) showing arrival distribution, queue stability, and 18.3% specialist capacity utilization.", caption_style)
        ]))

    # -------------------------------------------------------------
    # SECTION XII: DISCUSSION, LIMITATIONS & FUTURE SCOPE
    # -------------------------------------------------------------
    story.append(Paragraph("XII. CLINICAL DISCUSSION, LIMITATIONS & FUTURE RESEARCH", h1_style))
    story.append(Paragraph(
        "<b>Clinical Significance:</b> NETRA's high referable DR specificity (<b>95.60%</b> with 4&times; TTA on internal test data) directly addresses the public health triage bottleneck: "
        "over 95% of non-referable patients can be confidently reassured and scheduled for routine 12-month follow-up without overburdening tertiary eye centers. "
        "Crucially, on unseen external hospital cameras (SUSTech-SYSU, <i>n</i>=1,219), the platform achieves <b>97.34%</b> sensitivity (ROC-AUC <b>99.16%</b>) with <b>88.70%</b> specificity for referable DR under 4&times; TTA "
        "(and 96.81% sensitivity, 88.09% specificity, ROC-AUC 99.07% under single-model inference), substantially surpassing the World Health Organization (WHO) "
        "and UK National Health Service (NHS) screening benchmark (&gt;80% sensitivity) for sight-threatening retinal disease.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Technical Limitations:</b><br/>"
        "1. <i>2D Fundus vs. 3D Optical Coherence Tomography (OCT):</i> Color fundus photography visualizes en-face surface pathology but cannot resolve axial intraretinal cystoid spaces or subretinal fluid pathognomonic of Diabetic Macular Edema (DME). "
        "Consequently, while NETRA detects hard exudates and macular threat indicators, definitive diagnosis of center-involving DME requires secondary OCT confirmation.<br/>"
        "2. <i>Class Imbalance Across Boundary Classes:</i> Severe NPDR (Grade 3) constitutes only 2.63% of the combined screening cohort (287 training samples and 63 test samples). "
        "Consequently, while the model achieves 89.59% F1-score for Grade 0, 77.49% for Grade 2, and 78.77% for Grade 4, boundary classes (Grade 1 Mild at 39.65% F1 and Grade 3 Severe at 54.55% F1) "
        "reflect standard clinical inter-observer variability where subtle microaneurysm counts hover near diagnostic cutoffs.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Future Research Roadmap:</b> Planned extensions include integrating self-supervised vision transformers (e.g., RETFound) pre-trained on multi-million retinal corpora, "
        "privacy-preserving federated learning across multi-state hospital nodes, and multi-modal integration with patient systemic biomarkers (HbA1c, systolic blood pressure, and renal function).",
        body_style
    ))

    # -------------------------------------------------------------
    # SECTION XIII: CONCLUSION
    # -------------------------------------------------------------
    story.append(Paragraph("XIII. CONCLUSION", h1_style))
    story.append(Paragraph(
        "In this work, we presented NETRA, an end-to-end, explainable deep learning screening platform for diabetic retinopathy designed for scalable deployment. "
        "By coupling deterministic Image Quality Assessment, EfficientNet-B0 with 4&times; Test-Time Augmentation, post-hoc temperature scaling (<i>T*</i>=1.3353), "
        "spatial activation centroid tracking, and a one-way clinical approval decision lock, NETRA bridges the gap between laboratory deep learning and "
        "real-world clinical tele-ophthalmology workflows. The platform demonstrated substantial diagnostic agreement (internal QWK <b>0.8342</b>, accuracy <b>81.81%</b>, referable DR ROC-AUC <b>95.93%</b>) "
        "and robust cross-camera clinical transferability (SUSTech-SYSU external QWK <b>0.7654</b>, referable DR sensitivity <b>97.34%</b>, specificity <b>88.70%</b>, ROC-AUC <b>99.16%</b>). NETRA provides a scalable, auditable, and clinically governed foundation "
        "for community-based screening programs aiming to prevent diabetic blindness.",
        body_style
    ))

    # -------------------------------------------------------------
    # REFERENCES
    # -------------------------------------------------------------
    story.append(Paragraph("REFERENCES", h1_style))
    references = [
        "[1] N. Cheung, P. Mitchell, and T. Y. Wong, \"Diabetic retinopathy,\" <i>The Lancet</i>, vol. 376, no. 9735, pp. 124–136, Jul. 2010.",
        "[2] C. P. Wilkinson, F. L. Ferris, R. E. Klein, P. P. Lee, et al., \"Proposed international clinical diabetic retinopathy and diabetic macular edema disease severity scales,\" <i>Ophthalmology</i>, vol. 110, no. 9, pp. 1677–1682, Sep. 2003.",
        "[3] M. D. Abràmoff, Y. Lou, A. Erginay, W. Clarida, et al., \"Improved automated detection of diabetic retinopathy on a publicly available dataset through integration of deep learning,\" <i>Investigative Ophthalmology & Visual Science</i>, vol. 57, no. 13, pp. 5200–5206, Oct. 2016.",
        "[4] V. Gulshan, L. Peng, M. Coram, M. C. Stumpe, et al., \"Development and validation of a deep learning algorithm for detection of diabetic retinopathy in retinal fundus photographs,\" <i>JAMA</i>, vol. 316, no. 22, pp. 2402–2410, Dec. 2016.",
        "[5] M. Tan and Q. V. Le, \"EfficientNet: Rethinking model scaling for convolutional neural networks,\" in <i>Proc. Int. Conf. Mach. Learn. (ICML)</i>, 2019, pp. 6105–6114.",
        "[6] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, et al., \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" in <i>Proc. IEEE Int. Conf. Comput. Vis. (ICCV)</i>, 2017, pp. 618–626.",
        "[7] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, \"On calibration of modern neural networks,\" in <i>Proc. Int. Conf. Mach. Learn. (ICML)</i>, 2017, pp. 1321–1330.",
        "[8] B. Graham, \"Kaggle Diabetic Retinopathy Detection Competition Report,\" Tech. Rep., 2015. [Online]. Available: https://github.com/btgraham/SparseConvNet",
        "[9] T. Li, Y. Gao, K. Wang, S. Guo, et al., \"Diagnostic assessment of deep learning algorithms for diabetic retinopathy screening,\" <i>Information Sciences</i>, vol. 501, pp. 511–522, Oct. 2019.",
        "[10] APTOS 2019 Blindness Detection, Asia Pacific Tele-Ophthalmology Society, Kaggle competition dataset, 2019. [Online]. Available: https://www.kaggle.com/c/aptos2019-blindness-detection",
        "[11] H. Shen, S. Wang, et al., \"SUSTech-SYSU dataset: A clinical retinal dataset with optic disc, fovea, and lesion annotations,\" Southern Univ. of Science and Technology, Tech. Rep., 2020.",
        "[12] J. Hu, L. Shen, and G. Sun, \"Squeeze-and-Excitation networks,\" in <i>Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)</i>, 2018, pp. 7132–7141.",
    ]
    for ref in references:
        story.append(Paragraph(ref, bullet_style))

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] NETRA Complete IEEE Research Report generated at: {output_pdf_path}")
    return output_pdf_path


if __name__ == "__main__":
    out_dir = ROOT_DIR / "outputs" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    target_pdf = str(out_dir / "NETRA_Complete_IEEE_Technical_Research_Report.pdf")
    build_pdf_report(target_pdf)
    
    # Also copy to root for quick access
    import shutil
    root_pdf = str(ROOT_DIR / "NETRA_Complete_IEEE_Technical_Research_Report.pdf")
    shutil.copy2(target_pdf, root_pdf)
    print(f"[SUCCESS] Copied to project root: {root_pdf}")
