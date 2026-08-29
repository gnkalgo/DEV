import { StatusBadge } from "@/components/ui/terminal";

export function OrderStatusBadge({ status }: { status: string }) {
  return <StatusBadge status={status} />;
}
