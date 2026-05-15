import { useQuery, useMutation } from "@tanstack/react-query";
import { useAuth } from "../hooks/useAuth";
import { useT } from "../i18n/context";
import { langNames, type Lang } from "../i18n/translations";
import { getYtdlpVersion, updateYtdlp } from "../api/system";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

export default function SettingsPage() {
  const { t, lang, setLang } = useT();
  const { user } = useAuth();

  const { data: versionData, isLoading: versionLoading, refetch: refetchVersion } = useQuery({
    queryKey: ["ytdlp-version"],
    queryFn: getYtdlpVersion,
  });

  const updateMutation = useMutation({
    mutationFn: updateYtdlp,
    onSuccess: (data) => {
      if (data.ok) {
        toast.success(t("updateSuccess"));
        refetchVersion();
      } else {
        toast.error(data.error || t("updateFailed"));
      }
    },
    onError: (err: Error) => toast.error(err.message || t("updateFailed")),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">{t("settingsTitle")}</h2>

      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>{t("language")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="w-48 space-y-2">
            <Label>{t("language")}</Label>
            <Select value={lang} onValueChange={(v) => setLang(v as Lang)}>
              <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
              <SelectContent>
                {(Object.keys(langNames) as Lang[]).map((l) => (
                  <SelectItem key={l} value={l}>{langNames[l]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {user?.is_admin && (
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>{t("ytdlpVersion")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {versionLoading ? (
              <Skeleton className="h-6 w-32" />
            ) : versionData?.version ? (
              <p className="text-2xl font-mono font-bold">{versionData.version}</p>
            ) : (
              <p className="text-destructive">{versionData?.error || t("loadError")}</p>
            )}
            <Button
              variant="outline"
              disabled={updateMutation.isPending}
              onClick={() => updateMutation.mutate()}
            >
              {updateMutation.isPending ? t("updating") : t("updateYtdlp")}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
