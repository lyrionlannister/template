import { useId, useState, type DragEvent, type FC } from "react";
import { UploadCloud } from "lucide-react";
import type { FileDropzoneProps } from "../props/file-dropzone-props";
import { cn } from "../../shared/utils/cn";

export const FileDropzone: FC<FileDropzoneProps> = ({ label, hint, accept, onFilesSelected }) => {
  const inputId = useId();
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    if (event.dataTransfer.files.length > 0) onFilesSelected(event.dataTransfer.files);
  };

  return (
    <label
      htmlFor={inputId}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "block border-[1.5px] border-dashed rounded-md px-5 py-8.5 text-center bg-surface-2 text-ink-2 cursor-pointer transition-colors duration-fast ease-out",
        dragging ? "border-brand bg-brand-soft" : "border-border-strong",
      )}
    >
      <UploadCloud className="size-7.5 text-brand mx-auto mb-2" aria-hidden />
      <p className="text-[14.5px] font-semibold text-ink">{label}</p>
      {hint && <p className="text-[12.5px] mt-1">{hint}</p>}
      <input
        id={inputId}
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(event) => event.target.files && onFilesSelected(event.target.files)}
      />
    </label>
  );
};
