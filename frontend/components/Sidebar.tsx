"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
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
  LogOut
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

  return (
    <aside className="fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r border-slate-200 bg-white">
      {/* Brand Header */}
      <Link href="/" className="flex h-16 items-center gap-3 border-b border-slate-100 px-6 hover:bg-slate-50 transition-colors">
        <img
          src="/favicon.svg"
          alt="Client Magnet"
          className="h-8 w-8 drop-shadow-[0_0_8px_rgba(56,189,248,0.4)]"
        />
        <div>
          <span className="text-base font-black text-slate-900 tracking-tight block leading-tight">Client Magnet</span>
          <span className="text-[10px] text-sky-600 font-bold uppercase tracking-wider">Enterprise CRM</span>
        </div>
      </Link>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 px-4 py-4 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-semibold transition-all duration-200",
                isActive
                  ? "bg-indigo-50 text-indigo-600 font-bold"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 flex-shrink-0 transition-colors duration-200",
                  isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-500"
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
          onClick={() => logout()}
          className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition duration-150"
        >
          <LogOut className="h-4 w-4 text-rose-500" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
