import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useT } from "../i18n/context";
import { Button } from "@/components/ui/button";
import { Toaster } from "@/components/ui/sonner";
import { LayoutDashboard, ListTodo, Video, Cookie, Settings, Users, LogOut } from "lucide-react";

export default function Layout() {
  const { user, logout } = useAuth();
  const { t } = useT();
  const navigate = useNavigate();

  const navItems = [
    { to: "/", label: t("dashboard"), icon: LayoutDashboard },
    { to: "/tasks", label: t("tasks"), icon: ListTodo },
    { to: "/videos", label: t("videos"), icon: Video },
    { to: "/cookies", label: t("cookies"), icon: Cookie },
    ...(user?.is_admin
      ? [{ to: "/users", label: t("userManagement"), icon: Users }]
      : []),
    { to: "/settings", label: t("settings"), icon: Settings },
  ];

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-background">
      <aside className="w-56 border-r flex flex-col p-4 gap-2">
        <h1 className="text-lg font-bold mb-4">Vido</h1>
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors
              ${isActive ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
        <div className="mt-auto pt-4 border-t">
          <p className="text-xs text-muted-foreground px-3 mb-2">{user?.username}</p>
          <Button variant="ghost" size="sm" className="w-full justify-start" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" /> {t("logout")}
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
