import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getCookies, createCookie, deleteCookie, type CookieProfile, type CreateCookieInput } from "../api/cookies";
import { useT } from "../i18n/context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function CookiesPage() {
  const { t } = useT();
  const queryClient = useQueryClient();
  const [site, setSite] = useState("");
  const [sourceType, setSourceType] = useState<"file_upload" | "paste">("paste");
  const [cookieContent, setCookieContent] = useState("");
  const [cookieFile, setCookieFile] = useState<File | null>(null);

  const { data: cookies, isLoading } = useQuery({
    queryKey: ["cookies"],
    queryFn: getCookies,
  });

  const createMutation = useMutation({
    mutationFn: (input: CreateCookieInput) => createCookie(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cookies"] });
      setSite("");
      setCookieContent("");
      setCookieFile(null);
      toast.success(t("cookieSaved"));
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCookie(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cookies"] });
      toast.success(t("cookieDeleted"));
    },
  });

  const handleSubmit = async () => {
    if (!site.trim()) { toast.error(t("siteRequired")); return; }

    let content = "";
    if (sourceType === "paste") {
      content = cookieContent;
    } else if (cookieFile) {
      content = await cookieFile.text();
    }

    if (!content.trim()) { toast.error(t("contentRequired")); return; }

    createMutation.mutate({ site: site.trim(), source_type: sourceType, cookie_content: content });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">{t("cookiesTitle")}</h2>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="w-40 space-y-2">
              <Label>{t("site")}</Label>
              <Input placeholder="youtube" value={site} onChange={(e) => setSite(e.target.value)} />
            </div>
            <div className="w-40 space-y-2">
              <Label>{t("importMethod")}</Label>
              <Select value={sourceType} onValueChange={(v) => setSourceType(v as "file_upload" | "paste")}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="paste">{t("paste")}</SelectItem>
                  <SelectItem value="file_upload">{t("upload")}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSubmit} disabled={createMutation.isPending}>
              {createMutation.isPending ? t("saving") : t("addCookie")}
            </Button>
          </div>

          <Tabs value={sourceType} onValueChange={(v) => setSourceType(v as "file_upload" | "paste")}>
            <TabsList>
              <TabsTrigger value="paste">{t("paste")}</TabsTrigger>
              <TabsTrigger value="file_upload">{t("upload")}</TabsTrigger>
            </TabsList>
            <TabsContent value="paste" className="pt-4">
              <Label>{t("contentLabel")}</Label>
              <textarea
                className="w-full h-32 mt-2 p-3 border rounded-md text-sm font-mono bg-muted/50"
                placeholder={"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t1234567890\tLOGIN_INFO\t..."}
                value={cookieContent}
                onChange={(e) => setCookieContent(e.target.value)}
              />
            </TabsContent>
            <TabsContent value="file_upload" className="pt-4">
              <Label>{t("uploadLabel")}</Label>
              <Input type="file" className="mt-2" onChange={(e) => setCookieFile(e.target.files?.[0] || null)} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("site")}</TableHead>
              <TableHead>{t("importMethod")}</TableHead>
              <TableHead>{t("created")}</TableHead>
              <TableHead>{t("updated")}</TableHead>
              <TableHead>{t("actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {cookies?.map((c: CookieProfile) => (
              <TableRow key={c.id}>
                <TableCell><Badge variant="outline">{c.site}</Badge></TableCell>
                <TableCell>{c.source_type === "file_upload" ? t("upload") : t("paste")}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{new Date(c.created_at).toLocaleString()}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{new Date(c.updated_at).toLocaleString()}</TableCell>
                <TableCell>
                  <Button variant="ghost" size="sm" onClick={() => { if (confirm(t("confirmDelete"))) deleteMutation.mutate(c.id); }}>
                    {t("delete")}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {cookies?.length === 0 && (
              <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">{t("noCookies")}</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
