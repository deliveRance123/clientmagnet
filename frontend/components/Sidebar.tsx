"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useUI } from "@/lib/ui-context";
import { 
  LayoutDashboard, 
  Layers,
  Users, 
  Share2, 
  MessageSquare, 
  Phone,
  Mail, 
  Clock,
  Briefcase, 
  FileText, 
  Settings as SettingsIcon, 
  Magnet,
  LogOut,
  X
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "CRM Pipeline", href: "/crm", icon: Briefcase },
  { name: "Analytics", href: "/analytics", icon: Magnet },
  { name: "Clients", href: "/clients", icon: Users },
  { name: "Leads", href: "/leads", icon: Users },
  { name: "Services", href: "/services", icon: Layers },
  { name: "Messages", href: "/messages", icon: MessageSquare },
  { name: "Email", href: "/email", icon: Mail },
  { name: "WhatsApp", href: "/whatsapp", icon: Phone },
  { name: "Follow-Ups", href: "/follow-ups", icon: Clock },
  { name: "Social Content", href: "/content", icon: FileText },
  { name: "Social Accounts", href: "/social", icon: Share2 },
  { name: "Settings", href: "/settings", icon: SettingsIcon },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { sidebarOpen, closeSidebar } = useUI();

  const getInitials = (name?: string | null, email?: string) => {
    if (name && name.trim()) {
      const parts = name.trim().split(" ");
      return parts.length > 1
        ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
        : parts[0].slice(0, 2).toUpperCase();
    }
    if (email) {
      return email.slice(0, 2).toUpperCase();
    }
    return "CM";
  };

  const navContent = (
    <div className="flex h-full flex-col bg-white">
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between border-b border-slate-100 px-6">
        <Link
          href="/"
          onClick={closeSidebar}
          className="flex items-center gap-3 hover:opacity-90 transition-opacity"
        >
          <img
            src="/favicon.svg"
            alt="Client Magnet"
            width={32}
            height={32}
            style={{ width: "32px", height: "32px", maxWidth: "32px", maxHeight: "32px" }}
            className="h-8 w-8 drop-shadow-[0_0_8px_rgba(56,189,248,0.4)]"
          />
          <div>
            <span className="text-base font-black text-slate-900 tracking-tight block leading-tight">
              Client Magnet
            </span>
            <span className="text-[10px] text-sky-600 font-bold uppercase tracking-wider">
              Enterprise CRM
            </span>
          </div>
        </Link>
        {/* Mobile Close Button */}
        <button
          onClick={closeSidebar}
          className="md:hidden rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 px-4 py-4 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={closeSidebar}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-semibold transition-all duration-200",
                isActive
                  ? "bg-indigo-50 text-indigo-600 font-bold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 flex-shrink-0 transition-colors duration-200",
                  isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-600"
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Footer Profile & Sign Out */}
      <div className="border-t border-slate-100 p-4 space-y-3">
        <div className="flex items-center gap-3 px-1">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-600 to-sky-500 text-xs font-bold text-white shadow-sm">
            {getInitials(user?.full_name, user?.email)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-bold text-slate-800">
              {user?.full_name || user?.email?.split("@")[0] || "User"}
            </p>
            <p className="truncate text-[11px] text-slate-400">
              {user?.company_name || user?.email || "Workspace"}
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            closeSidebar();
            logout();
          }}
          className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition duration-150"
        >
          <LogOut className="h-4 w-4 text-rose-500" />
          Sign Out
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Sidebar */}
      <aside className="hidden md:flex fixed inset-y-0 left-0 z-30 w-64 flex-col border-r border-slate-200 bg-white">
        {navContent}
      </aside>

      {/* Mobile Backdrop & Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs transition-opacity animate-in fade-in"
            onClick={closeSidebar}
          />
          {/* Slide-out Drawer */}
          <aside className="relative flex w-72 max-w-[85vw] flex-col bg-white shadow-2xl z-10 border-r border-slate-200 animate-in slide-in-from-left duration-200">
            {navContent}
          </aside>
        </div>
      )}
    </>
  );
}
