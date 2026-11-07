export interface StepperStep {
  label: string;
}

export interface StepperProps {
  steps: StepperStep[];
  currentIndex: number;
}
