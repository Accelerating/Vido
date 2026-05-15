import React, { useState, type FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getTasks, createTask, deleteTask, fetchFormats, type Task, type FormatInfo, type CreateTaskInput, type ListFormatsInput } from "../api/tasks";
import { getCookies, type CookieProfile } from "../api/cookies";
import { useT } from "../i18n/context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "secondary",
  downloading: "default",
  completed: "outline",
  failed: "destructive",
};

const statusKeys = ["pending", "downloading", "completed", "failed"] as const;

export default function TasksPage() {
  const { t } = useT();
  const queryClient = useQueryClient();
  const [url, setUrl] = useState("");
  const [cookieProfileId, setCookieProfileId] = useState<string>("none");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [expandedLog, setExpandedLog] = useState<number | null>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [formats, setFormats] = useState<FormatInfo[]>([]);
  const [selectedFormat, setSelectedFormat] = useState<string>("");
  const [loadingFormats, setLoadingFormats] = useState(false);
  const [formatError, setFormatError] = useState("");

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["tasks", statusFilter],
    queryFn: () => getTasks(statusFilter === "all" ? undefined : statusFilter),
    refetchInterval: 3000,
  });

  const { data: cookies } = useQuery({
    queryKey: ["cookies"],
    queryFn: getCookies,
  });

  const createMutation = useMutation({
    mutationFn: (input: CreateTaskInput) => createTask(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      setUrl("");
      setDialogOpen(false);
      setFormats([]);
      setSelectedFormat("");
      toast.success(t("taskCreated"));
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      toast.success(t("taskDeleted"));
    },
  });

  const handleOpenDialog = async (e: FormEvent) => {
    e.preventDefault();
    if (!url.trim()) { toast.error(t("urlRequired")); return; }

    setDialogOpen(true);
    setLoadingFormats(true);
    setFormatError("");
    setFormats([]);
    setSelectedFormat("");

    try {
      const input: ListFormatsInput = { url: url.trim() };
      if (cookieProfileId !== "none") input.cookie_profile_id = parseInt(cookieProfileId);
      const result = await fetchFormats(input);
      if (result.length === 0) {
        setFormatError(t("noFormats"));
      } else {
        setFormats(result);
        const best = result.find((f) => f.acodec !== "video only" && f.acodec !== "audio only" && f.vcodec !== "video only") || result[0];
        setSelectedFormat(best.code);
      }
    } catch (err: any) {
      setFormatError(err.message || t("fetchFormatsFailed"));
    } finally {
      setLoadingFormats(false);
    }
  };

  const handleConfirmDownload = () => {
    if (!selectedFormat) { toast.error(t("selectFirst")); return; }
    const input: CreateTaskInput = { url: url.trim(), quality: "1080p", format: selectedFormat };
    if (cookieProfileId !== "none") input.cookie_profile_id = parseInt(cookieProfileId);
    createMutation.mutate(input);
  };

  const statusLabel = (s: string) =>
    s === "pending" ? t("pending") : s === "downloading" ? t("downloading") : s === "completed" ? t("completed") : t("failed");

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">{t("tasksTitle")}</h2>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleOpenDialog} className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[300px] space-y-2">
              <Label>{t("videoUrl")}</Label>
              <Input className="h-9" placeholder={t("urlPlaceholder")} value={url} onChange={(e) => setUrl(e.target.value)} required />
            </div>
            <div className="w-40 space-y-2">
              <Label>{t("cookieOptional")}</Label>
              <Select value={cookieProfileId} onValueChange={setCookieProfileId}>
                <SelectTrigger className="h-9"><SelectValue placeholder={t("cookieNone")} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">{t("cookieNone")}</SelectItem>
                  {cookies?.map((c: CookieProfile) => (
                    <SelectItem key={c.id} value={String(c.id)}>{c.site} (#{c.id})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="opacity-0 pointer-events-none">.</Label>
              <Button type="submit" disabled={createMutation.isPending} className="h-9">
                {t("startDownload")}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => { if (!createMutation.isPending) { setDialogOpen(false); setFormats([]); } }}>
          <Card className="w-full max-w-3xl max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <CardContent className="pt-6 flex-1 overflow-hidden flex flex-col">
              <h3 className="text-lg font-bold mb-2">{t("selectFormat")}</h3>
              <p className="text-sm text-muted-foreground mb-3 truncate">{url}</p>

              {loadingFormats ? (
                <div className="space-y-2 py-8">
                  <Skeleton className="h-6 w-48" /><Skeleton className="h-6 w-full" /><Skeleton className="h-6 w-full" /><Skeleton className="h-6 w-full" />
                </div>
              ) : formatError ? (
                <div className="py-8 text-center">
                  <p className="text-destructive mb-3">{formatError}</p>
                  <Button variant="outline" onClick={() => setDialogOpen(false)}>{t("close")}</Button>
                </div>
              ) : (
                <>
                  <div className="flex-1 overflow-auto border rounded-md">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-10">{t("select")}</TableHead>
                          <TableHead>{t("codec")}</TableHead>
                          <TableHead>{t("resolution")}</TableHead>
                          <TableHead>{t("ext")}</TableHead>
                          <TableHead>{t("size")}</TableHead>
                          <TableHead>{t("note")}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {formats.map((f) => (
                          <TableRow key={f.code} className={`cursor-pointer hover:bg-muted ${selectedFormat === f.code ? "bg-primary/10" : ""}`} onClick={() => setSelectedFormat(f.code)}>
                            <TableCell><input type="radio" name="format" checked={selectedFormat === f.code} onChange={() => setSelectedFormat(f.code)} /></TableCell>
                            <TableCell className="font-mono text-xs">{f.vcodec}+{f.acodec}</TableCell>
                            <TableCell>{f.resolution}{f.fps ? ` ${f.fps}fps` : ""}</TableCell>
                            <TableCell className="font-mono text-xs">{f.ext}</TableCell>
                            <TableCell className="text-xs whitespace-nowrap">{f.file_size || f.tbr || "-"}</TableCell>
                            <TableCell className="text-xs text-muted-foreground">{f.note}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <div className="flex gap-3 justify-end mt-4">
                    <Button variant="outline" onClick={() => { setDialogOpen(false); setFormats([]); }} disabled={createMutation.isPending}>
                      {t("cancel")}
                    </Button>
                    <Button onClick={handleConfirmDownload} disabled={!selectedFormat || createMutation.isPending}>
                      {createMutation.isPending ? t("creating") : t("confirmDownload")}
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <div className="flex gap-2">
        {["all", ...statusKeys].map((s) => (
          <Badge key={s} variant={statusFilter === s ? "default" : "outline"} className="cursor-pointer" onClick={() => setStatusFilter(s)}>
            {s === "all" ? t("all") : statusLabel(s)}
          </Badge>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2"><Skeleton className="h-10" /><Skeleton className="h-10" /><Skeleton className="h-10" /></div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("titleLink")}</TableHead>
              <TableHead>{t("status")}</TableHead>
              <TableHead>{t("format")}</TableHead>
              <TableHead>{t("created")}</TableHead>
              <TableHead>{t("actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks?.map((task: Task) => (
              <React.Fragment key={task.id}>
                <TableRow>
                  <TableCell className="max-w-[300px] truncate">{task.title || task.url}</TableCell>
                  <TableCell><Badge variant={statusVariant[task.status] || "secondary"}>{statusLabel(task.status)}</Badge></TableCell>
                  <TableCell className="font-mono text-xs">{task.format_desc || task.format || "-"}</TableCell>
                  <TableCell className="text-muted-foreground text-sm">{new Date(task.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {task.log && (
                        <Button variant="ghost" size="sm" onClick={() => setExpandedLog(expandedLog === task.id ? null : task.id)}>
                          {expandedLog === task.id ? t("collapseLog") : t("expandLog")}
                        </Button>
                      )}
                      <Button variant="ghost" size="sm" onClick={() => { if (confirm(t("confirmDelete"))) deleteMutation.mutate(task.id); }}>
                        {t("delete")}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
                {expandedLog === task.id && task.log && (
                  <TableRow key={`${task.id}-log`}>
                    <TableCell colSpan={5} className="bg-muted/30">
                      <pre className="text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-96 overflow-y-auto p-3 bg-black text-green-400 rounded">
                        {task.log}
                      </pre>
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            ))}
            {tasks?.length === 0 && (
              <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">{t("noTasks")}</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
