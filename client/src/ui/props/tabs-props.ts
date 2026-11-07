export interface TabsOption {
  value: string;
  label: string;
}

export interface TabsProps {
  options: TabsOption[];
  value: string;
  onChange: (value: string) => void;
}
