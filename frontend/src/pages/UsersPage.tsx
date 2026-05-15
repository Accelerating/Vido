import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../hooks/useAuth";
import {
  getUsers, createUser, updateUser, deleteUser,
  type UserProfile, type CreateUserInput, type UpdateUserInput,
} from "../api/users";
import { useT } from "../i18n/context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

export default function UsersPage() {
  const { t } = useT();
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserProfile | null>(null);
  const [formUsername, setFormUsername] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formIsAdmin, setFormIsAdmin] = useState("false");

  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: getUsers,
  });

  const openCreate = () => {
    setEditingUser(null);
    setFormUsername("");
    setFormPassword("");
    setFormIsAdmin("false");
    setDialogOpen(true);
  };

  const openEdit = (u: UserProfile) => {
    setEditingUser(u);
    setFormUsername(u.username);
    setFormPassword("");
    setFormIsAdmin(u.is_admin ? "true" : "false");
    setDialogOpen(true);
  };

  const createMutation = useMutation({
    mutationFn: (input: CreateUserInput) => createUser(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setDialogOpen(false);
      toast.success(t("userCreated"));
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: UpdateUserInput }) => updateUser(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setDialogOpen(false);
      toast.success(t("userUpdated"));
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast.success(t("userDeleted"));
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const handleSubmit = () => {
    if (!formUsername.trim()) return;

    if (editingUser) {
      const input: UpdateUserInput = { username: formUsername.trim() };
      if (formPassword) input.password = formPassword;
      input.is_admin = formIsAdmin === "true";
      updateMutation.mutate({ id: editingUser.id, input });
    } else {
      if (!formPassword) return;
      createMutation.mutate({
        username: formUsername.trim(),
        password: formPassword,
        is_admin: formIsAdmin === "true",
      });
    }
  };

  const handleDelete = (u: UserProfile) => {
    if (u.id === currentUser?.id) {
      toast.error(t("userDeleteSelf"));
      return;
    }
    if (confirm(t("confirmDelete"))) {
      deleteMutation.mutate(u.id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">{t("userManagement")}</h2>
        <Button onClick={openCreate}>{t("userCreate")}</Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>{t("username")}</TableHead>
              <TableHead>{t("userAdmin")}</TableHead>
              <TableHead>{t("created")}</TableHead>
              <TableHead>{t("actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users?.map((u: UserProfile) => (
              <TableRow key={u.id}>
                <TableCell className="text-sm text-muted-foreground">{u.id}</TableCell>
                <TableCell>{u.username}</TableCell>
                <TableCell>
                  <Badge variant={u.is_admin ? "default" : "outline"}>
                    {u.is_admin ? t("yes") : t("no")}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(u.created_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => openEdit(u)}>
                      {t("edit")}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={u.id === currentUser?.id}
                      onClick={() => handleDelete(u)}
                    >
                      {t("delete")}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {users?.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  {t("noUsers")}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}

      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-sm">
            <CardHeader>
              <CardTitle>{editingUser ? t("userEdit") : t("userCreate")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{t("username")}</Label>
                <Input
                  value={formUsername}
                  onChange={(e) => setFormUsername(e.target.value)}
                  minLength={2}
                  maxLength={50}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>
                  {editingUser ? t("userPasswordOptional") : t("password")}
                </Label>
                <Input
                  type="password"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  minLength={editingUser ? undefined : 4}
                  required={!editingUser}
                />
              </div>
              <div className="space-y-2">
                <Label>{t("userAdmin")}</Label>
                <Select value={formIsAdmin} onValueChange={setFormIsAdmin}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">{t("yes")}</SelectItem>
                    <SelectItem value="false">{t("no")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setDialogOpen(false)}>
                  {t("cancel")}
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? t("saving")
                    : editingUser
                      ? t("save")
                      : t("userCreate")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
