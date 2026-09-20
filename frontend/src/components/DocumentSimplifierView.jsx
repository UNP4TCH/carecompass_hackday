import { useState, useRef } from "react";
import { Alert, ArrowRight, Check, FileText, Restart, UploadCloud, XIcon } from "./icons";
import { useFocusOnMount } from "../lib/useFocusOnMount";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];

function formatFileSize(bytes) {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isUnclear(val) {
  if (!val) return true;
  const s = val.toLowerCase();
  return s.includes("could not be read") || s.includes("unclear") || s.includes("illegible");
}

function isNotSpecified(val) {
  if (!val) return true;
  const s = val.toLowerCase();
  return s.includes("not specified") || s === "none" || s === "—";
}

function InstructionField({ label, value, highlightUnclear = true }) {
  const unclear = highlightUnclear && isUnclear(value);
  const notSpecified = isNotSpecified(value);

  if (notSpecified && !unclear) {
    return (
      <div className="doc-field">
        <dt className="doc-field-label">{label}</dt>
        <dd className="doc-field-value muted">Not specified in document</dd>
      </div>
    );
  }

  return (
    <div className={`doc-field${unclear ? " is-unclear" : ""}`}>
      <dt className="doc-field-label">{label}</dt>
      <dd className="doc-field-value">
        {unclear ? (
          <span className="unclear-badge">
            <Alert width={14} height={14} />
            Could not read clearly
          </span>
        ) : (
          value
        )}
      </dd>
    </div>
  );
}

export default function DocumentSimplifierView({ onBackToAssessment }) {
  const headingRef = useFocusOnMount();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);

  function resetAll() {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setLoading(false);
    setError(null);
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleFileSelected(file) {
    setError(null);

    if (!file) return;

    if (!ACCEPTED_TYPES.includes(file.type)) {
      const ext = file.name.split(".").pop()?.toLowerCase();
      if (!["jpg", "jpeg", "png", "webp"].includes(ext)) {
        setError("Unsupported file format. Please upload a JPEG, PNG, or WEBP photo.");
        return;
      }
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError("File size exceeds 10 MB limit. Please select a smaller photo.");
      return;
    }

    if (file.size === 0) {
      setError("The selected file is empty. Please choose a valid image.");
      return;
    }

    setSelectedFile(file);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    const objUrl = URL.createObjectURL(file);
    setPreviewUrl(objUrl);
  }

  function onFileChange(event) {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelected(file);
    }
  }

  function onDrop(event) {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      handleFileSelected(file);
    }
  }

  function onDragOver(event) {
    event.preventDefault();
    setIsDragOver(true);
  }

  function onDragLeave(event) {
    event.preventDefault();
    setIsDragOver(false);
  }

  async function handleSimplify() {
    if (!selectedFile || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${API_URL}/api/document/simplify`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.message || "Failed to analyze the document. Please try again.");
        return;
      }

      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Unable to connect to the server. Please check your backend connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="view document-view" aria-labelledby="doc-heading">
      <div className="doc-body">
        {/* VIEW HEADER */}
        <div className="doc-head">
          <p className="kicker kicker-tone">CareCompass · Document simplifier</p>
          <h1 id="doc-heading" ref={headingRef} tabIndex={-1} className="result-title focus-target">
            Understand your prescription
          </h1>
          <p className="lead">
            Upload a prescription, discharge note, or medication instruction sheet to make its written instructions easier to understand.
          </p>
        </div>

        {/* ERROR BANNER */}
        {error && (
          <div className="error-banner" role="alert">
            <Alert width={16} height={16} />
            <span>{error}</span>
          </div>
        )}

        {/* LOADING STATE */}
        {loading && (
          <div className="doc-loading-panel" role="status" aria-live="polite">
            <div className="loading-spinner" aria-hidden="true" />
            <h2 className="loading-title">Reading your document…</h2>
            <p className="muted">
              Extracting written medication names, dosages, and instructions into plain language…
            </p>
          </div>
        )}

        {/* UPLOAD PANEL (when not showing result and not loading) */}
        {!result && !loading && (
          <div className="doc-upload-panel">
            {!selectedFile ? (
              <div
                className={`doc-dropzone${isDragOver ? " is-dragover" : ""}`}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    fileInputRef.current?.click();
                  }
                }}
                aria-label="Upload prescription photo or discharge note"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                  onChange={onFileChange}
                  className="sr-only"
                />
                <div className="dropzone-icon" aria-hidden="true">
                  <UploadCloud width={36} height={36} />
                </div>
                <p className="dropzone-primary">
                  <strong>Choose a document photo</strong> or drag and drop here
                </p>
                <p className="dropzone-hint">
                  Supported formats: JPG, PNG, WEBP · Up to 10 MB
                </p>
              </div>
            ) : (
              <div className="doc-file-card">
                {previewUrl && (
                  <div className="doc-preview-thumb">
                    <img src={previewUrl} alt="Selected document preview" />
                  </div>
                )}
                <div className="doc-file-info">
                  <p className="doc-file-name">
                    <FileText width={18} height={18} />
                    <strong>{selectedFile.name}</strong>
                  </p>
                  <p className="doc-file-meta">
                    {formatFileSize(selectedFile.size)} · Ready to simplify
                  </p>
                  <div className="doc-file-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleSimplify}
                      disabled={loading}
                    >
                      Simplify document
                      <ArrowRight />
                    </button>
                    <button
                      type="button"
                      className="btn btn-quiet"
                      onClick={resetAll}
                      disabled={loading}
                    >
                      <XIcon width={16} height={16} />
                      Choose different file
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="doc-guidance-card">
              <h3>Tips for best results</h3>
              <ul>
                <li>Ensure good overhead lighting without strong shadows or camera glare.</li>
                <li>Keep the entire prescription or medication table visible in the frame.</li>
                <li>Hold the camera steady so that doctor handwriting and numbers are sharp.</li>
              </ul>
              <p className="fine">
                CareCompass processes your image securely in server memory and does not store or share your medical document.
              </p>
            </div>
          </div>
        )}

        {/* RESULTS PANEL */}
        {result && !loading && (
          <div className="doc-result-panel">
            {/* UNREADABLE OR NON-MEDICAL HANDLING */}
            {result.status === "unreadable" && (
              <div className="doc-alert-box tone-amber" role="alert">
                <div className="doc-alert-head">
                  <Alert width={20} height={20} />
                  <h2>Document could not be read clearly</h2>
                </div>
                <p>
                  {result.legibility_summary ||
                    "The handwriting or printed text in the uploaded photo is blurry, obscured, or illegible."}
                </p>
                <p className="muted">
                  Please take another photo with better lighting and sharp focus, or consult your pharmacist directly.
                </p>
              </div>
            )}

            {result.status === "not_a_medical_document" && (
              <div className="doc-alert-box tone-amber" role="alert">
                <div className="doc-alert-head">
                  <Alert width={20} height={20} />
                  <h2>No prescription or medical instructions detected</h2>
                </div>
                <p>
                  {result.legibility_summary ||
                    "The uploaded image does not appear to be a prescription, hospital discharge note, or medication instruction sheet."}
                </p>
                <p className="muted">
                  Please upload an image of a medical document to simplify its instructions.
                </p>
              </div>
            )}

            {result.status === "no_medications_found" && (
              <div className="doc-alert-box tone-amber" role="alert">
                <div className="doc-alert-head">
                  <Alert width={20} height={20} />
                  <h2>No medication instructions detected</h2>
                </div>
                <p>
                  We could read the document, but no specific medication or dosage instructions were identified.
                </p>
              </div>
            )}

            {/* MEDICATIONS LIST */}
            {result.medications && result.medications.length > 0 && (
              <div className="medications-section">
                <div className="section-header-row">
                  <h2 className="section-label">YOUR MEDICATIONS</h2>
                  <span className="med-count">
                    {result.medications.length} {result.medications.length === 1 ? "medication" : "medications"} found
                  </span>
                </div>

                <div className="medication-cards">
                  {result.medications.map((med, index) => {
                    const nameUnclear = isUnclear(med.name);
                    return (
                      <article key={index} className="med-card">
                        <div className="med-card-header">
                          <h3 className="med-name">
                            {nameUnclear ? (
                              <span className="unclear-badge">
                                <Alert width={16} height={16} />
                                Medication name could not be read clearly
                              </span>
                            ) : (
                              med.name
                            )}
                          </h3>
                          {med.strength && !isNotSpecified(med.strength) && (
                            <span className="strength-chip">
                              {isUnclear(med.strength) ? "Strength unclear" : med.strength}
                            </span>
                          )}
                        </div>

                        <dl className="med-grid">
                          <InstructionField
                            label="How often"
                            value={med.frequency}
                          />
                          <InstructionField
                            label="Dosage"
                            value={med.dosage}
                          />
                          <InstructionField
                            label="When"
                            value={med.timing}
                          />
                          <InstructionField
                            label="Duration"
                            value={med.duration}
                          />
                          <InstructionField
                            label="Food"
                            value={med.food_instructions}
                          />
                          <InstructionField
                            label="How to take"
                            value={med.route}
                          />
                        </dl>

                        {/* Extra instructions & warnings */}
                        {med.other_instructions && !isNotSpecified(med.other_instructions) && (
                          <div className="med-extra-row">
                            <span className="extra-label">Instructions:</span>
                            <span className="extra-text">{med.other_instructions}</span>
                          </div>
                        )}

                        {med.warnings && !isNotSpecified(med.warnings) && (
                          <div className="med-extra-row is-warning">
                            <span className="extra-label">Precaution:</span>
                            <span className="extra-text">{med.warnings}</span>
                          </div>
                        )}

                        {med.notes && (
                          <div className="med-notes">
                            <small>{med.notes}</small>
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
              </div>
            )}

            {/* GENERAL INSTRUCTIONS */}
            {result.general_instructions && result.general_instructions.length > 0 && (
              <div className="doc-section">
                <h2 className="section-label">General care instructions</h2>
                <ul className="doc-instruction-list">
                  {result.general_instructions.map((item, idx) => (
                    <li key={idx}>
                      <Check width={16} height={16} />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* GENERAL WARNINGS & PRECAUTIONS */}
            {result.warnings_and_precautions && result.warnings_and_precautions.length > 0 && (
              <div className="doc-section">
                <h2 className="section-label tone-text">Warnings & precautions written on document</h2>
                <ul className="doc-warning-list">
                  {result.warnings_and_precautions.map((item, idx) => (
                    <li key={idx}>
                      <Alert width={16} height={16} />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* MANDATORY DISCLAIMER & ACTIONS */}
            <div className="result-foot">
              <div className="disclaimer">
                <strong>Important</strong>
                <p>
                  {result.disclaimer ||
                    "CareCompass simplifies information written on your document. It does not replace instructions from your doctor or pharmacist."}
                </p>
              </div>

              <div className="doc-result-actions">
                <button type="button" className="btn btn-primary" onClick={resetAll}>
                  <Restart />
                  Simplify another document
                </button>
                {onBackToAssessment && (
                  <button type="button" className="btn btn-quiet" onClick={onBackToAssessment}>
                    Go to symptom guidance
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
