import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getVideos, getThumbnailUrl, type Video } from "../api/videos";
import { useT } from "../i18n/context";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

function formatBytes(bytes: number) {
  if (!bytes) return "";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export default function VideosPage() {
  const { t } = useT();
  const { data: videos, isLoading } = useQuery({
    queryKey: ["videos"],
    queryFn: getVideos,
  });

  if (isLoading) {
    return <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[1,2,3,4].map(i => <Skeleton key={i} className="h-48" />)}
    </div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">{t("videosTitle")}</h2>
      {videos?.length === 0 ? (
        <p className="text-muted-foreground">{t("noVideos")}</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {videos?.map((v: Video) => (
            <Link key={v.id} to={`/videos/${v.id}`}>
              <Card className="hover:shadow-lg transition-shadow h-full">
                <CardContent className="p-0">
                  <div className="aspect-video bg-muted rounded-t-xl flex items-center justify-center overflow-hidden">
                    {v.has_thumbnail ? (
                      <img src={getThumbnailUrl(v.id)} alt={v.title || t("unnamedVideo")} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-muted-foreground text-sm">{t("noThumbnail")}</span>
                    )}
                  </div>
                  <div className="p-3">
                    <p className="font-medium text-sm truncate">{v.title || t("unnamedVideo")}</p>
                    <p className="text-xs text-muted-foreground">{formatBytes(v.file_size || 0) || t("unknownSize")}</p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
