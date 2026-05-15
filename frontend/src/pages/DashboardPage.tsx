import { useQuery } from "@tanstack/react-query";
import { getStats } from "../api/stats";
import { useT } from "../i18n/context";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

function formatBytes(bytes: number) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export default function DashboardPage() {
  const { t } = useT();
  const { data, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <div className="space-y-4"><Skeleton className="h-24" /><Skeleton className="h-24" /></div>;
  }

  if (!data) return <p>{t("loadError")}</p>;

  const cards = [
    { title: t("pending"), value: data.tasks_pending, color: "text-blue-500" },
    { title: t("downloading"), value: data.tasks_downloading, color: "text-yellow-500" },
    { title: t("completed"), value: data.tasks_completed, color: "text-green-500" },
    { title: t("failed"), value: data.tasks_failed, color: "text-red-500" },
    { title: t("videoCount"), value: data.videos_count, color: "text-purple-500" },
  ];

  const used = data.disk_total_bytes - data.disk_free_bytes;
  const pct = data.disk_total_bytes > 0 ? ((used / data.disk_total_bytes) * 100).toFixed(1) : 0;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">{t("dashboardTitle")}</h2>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {cards.map(({ title, value, color }) => (
          <Card key={title}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-3xl font-bold ${color}`}>{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{t("diskUsage")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-lg">
            {formatBytes(used)} / {formatBytes(data.disk_total_bytes)} ({pct}%)
          </p>
          <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-primary transition-all" style={{ width: `${Math.min(Number(pct), 100)}%` }} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
