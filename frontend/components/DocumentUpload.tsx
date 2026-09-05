"use client";

import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { uploadDocumentRequest } from "@/services/api";
import type { SupportingDocument } from "@/types";

interface DocumentUploadProps {
  investigationId?: string;
  onUploaded?: (document: SupportingDocument) => void;
}

export function DocumentUpload({ investigationId, onUploaded }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState(false);

  const upload = async () => {
    setError(false);
    setMessage(null);
    if (!investigationId?.trim()) {
      setError(true);
      setMessage("A valid investigation ID is required before uploading a document.");
      return;
    }
    if (!selectedFile) {
      setError(true);
      setMessage("Select a document before uploading.");
      return;
    }
    if (selectedFile.size === 0) {
      setError(true);
      setMessage("The selected document is empty. Choose a non-empty file and try again.");
      return;
    }

    setUploading(true);
    try {
      const document = await uploadDocumentRequest(investigationId, selectedFile);
      setMessage(`${document.file_name ?? selectedFile.name} uploaded successfully. Processing status: ${document.processing_status}.`);
      setSelectedFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onUploaded?.(document);
    } catch (reason: unknown) {
      setError(true);
      setMessage(reason instanceof Error ? reason.message : "The document could not be uploaded. Try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <section className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-surface-dark" aria-labelledby="document-upload-title">
      <div className="flex items-center gap-3 border-b border-gray-100 px-6 py-4 dark:border-gray-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300"><Upload className="h-5 w-5" /></div>
        <h3 id="document-upload-title" className="text-base font-semibold text-gray-900 dark:text-white">Upload supporting document</h3>
      </div>
      <div className="space-y-3 px-6 py-5">
        <input ref={inputRef} type="file" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} disabled={uploading} className="block w-full text-sm text-gray-600 dark:text-gray-300" />
        <button type="button" onClick={upload} disabled={uploading || !selectedFile} className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">
          {uploading ? "Uploading…" : "Upload document"}
        </button>
        {message && <p role="status" className={`text-sm ${error ? "text-red-700" : "text-emerald-700"}`}>{message}</p>}
      </div>
    </section>
  );
}
