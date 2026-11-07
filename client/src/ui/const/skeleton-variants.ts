import type { SkeletonVariant } from "../props/skeleton-props";

export const SKELETON_VARIANT_CLASSES: Record<SkeletonVariant, string> = {
  text: "h-3 rounded-sm",
  title: "h-4.5 rounded-sm",
  circle: "rounded-full",
  block: "rounded-sm",
};
