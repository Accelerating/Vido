import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getVideos, getVideoStreamUrl, type Video } from "../api/videos";
import { useT } from "../i18n/context";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronLeft } from "lucide-react";

export default function VideoPlayerPage() {
  const { t } = useT();
  const { id } = useParams<{ id: string }>();
  const { data: videos } = useQuery({
    queryKey: ["videos"],
    queryFn: getVideos,
  });

  const video: Video | undefined = videos?.find((v: Video) => v.id === Number(id));

  if (!video) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="aspect-video w-full max-w-4xl" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link to="/videos">
          <Button variant="ghost" size="sm"><ChevronLeft className="h-4 w-4 mr-1" /> {t("back")}</Button>
        </Link>
        <h2 className="text-xl font-bold truncate">{video.title || t("unnamedVideo")}</h2>
      </div>
      <video className="w-full max-w-4xl rounded-lg bg-black" controls autoPlay src={getVideoStreamUrl(video.id)}>
        {t("unsupportedVideo")}
      </video>
    </div>
  );
}
