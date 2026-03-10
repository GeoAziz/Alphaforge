import { cn } from "@/lib/utils";

interface ConfidencePillProps {
  score: number;
}

export function ConfidencePill({ score }: ConfidencePillProps) {
  let colorClass = "bg-red/10 text-red border-red/20";
  let dotClass = "bg-red";

  if (score >= 80) {
    colorClass = "bg-green/10 text-green border-green/20 shadow-[0_0_12px_rgba(52,211,153,0.15)]";
    dotClass = "bg-green";
  } else if (score >= 60) {
    colorClass = "bg-amber/10 text-amber border-amber/20";
    dotClass = "bg-amber";
  }

  return (
    <div className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-bold tracking-wider uppercase",
      colorClass
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", dotClass)} />
      {score}% CONFIDENCE
    </div>
  );
}
