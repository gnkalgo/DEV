import { Skeleton } from "@/components/ui/terminal";

export function ChartLoading() {
  return (
    <div className="space-y-2 p-3">
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-[280px] w-full" />
      <Skeleton className="h-[80px] w-full" />
    </div>
  );
}
