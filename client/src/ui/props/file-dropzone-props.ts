export interface FileDropzoneProps {
  label: string;
  hint?: string;
  accept?: string;
  onFilesSelected: (files: FileList) => void;
}
