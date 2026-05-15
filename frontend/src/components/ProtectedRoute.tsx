import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useT } from "../i18n/context";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const { t } = useT();

  if (loading) return <div className="flex h-screen items-center justify-center">{t("loading")}</div>;
  if (!user) return <Navigate to="/login" replace />;

  return <>{children}</>;
}
