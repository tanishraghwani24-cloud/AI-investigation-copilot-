import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
}

export function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      {Icon && (
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 text-gray-400">
          <Icon className="h-5 w-5" />
        </div>
      )}
      <h4 className="text-sm font-medium text-gray-900">{title}</h4>
      <p className="mt-1 text-sm text-gray-500 max-w-sm">{description}</p>
    </div>
  );
}
