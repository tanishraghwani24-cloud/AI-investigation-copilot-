import { InvestigationDetails } from "@/components/investigations/InvestigationDetails";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function InvestigationDetailPage({ params }: PageProps) {
  const { id } = await params;
  return <InvestigationDetails id={decodeURIComponent(id)} />;
}
