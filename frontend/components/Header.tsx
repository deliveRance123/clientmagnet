"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useUI } from "@/lib/ui-context";
import {
  getNotifications,
  globalSearch,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/api";
import { GlobalSearchResultItem, NotificationItem } from "@/types";
import {
  Bell,
  CheckCheck,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  Briefcase,
  MessageSquare,
  Mail,
  Loader2,
  X,
  Menu,
} from "lucide-react";

export default function Header() {
  const pathname = usePathname();
  const { user, token } = useAuth();
  const { toggleSidebar } = useUI();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [showDropdown, setShowDropdown] = useState<boolean>(false);

  // Global Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GlobalSearchResultItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);

  const loadNotifications = async () => {
    if (!token) return;
    try {
      const data = await getNotifications(token, false);
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch {
      // Graceful fallback
    }
  };

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, [token]);

  const handleMarkAllRead = async () => {
    if (!token) return;
    try {
      await markAllNotificationsRead(token);
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  };

  const handleNotificationClick = async (notif: NotificationItem) => {
    if (!token) return;
    if (!notif.is_read) {
      await markNotificationRead(token, notif.id);
      setUnreadCount((c) => Math.max(0, c - 1));
      setNotifications((prev) =>
        prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
      );
    }
    setShowDropdown(false);
  };

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !searchQuery.trim()) return;

    try {
      setSearching(true);
      setShowSearchModal(true);
      const res = await globalSearch(token, searchQuery.trim(), 15);
      setSearchResults(res.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  // Convert pathname to readable title
  const getTitle = () => {
    if (pathname === "/") return "Dashboard Overview";
    const path = pathname.replace("/", "");
    return path.charAt(0).toUpperCase() + path.slice(1).replace("-", " ");
  };

  const renderEntityIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "lead":
        return <Users className="h-4 w-4 text-indigo-600" />;
      case "client":
        return <Briefcase className="h-4 w-4 text-emerald-600" />;
      case "conversation":
        return <MessageSquare className="h-4 w-4 text-sky-600" />;
      case "message":
        return <Mail className="h-4 w-4 text-amber-600" />;
      default:
        return <Sparkles className="h-4 w-4 text-slate-500" />;
    }
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/90 backdrop-blur-md px-4 sm:px-6 md:px-8">
      {/* Left: Mobile Hamburger & Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="md:hidden rounded-lg p-2 text-slate-600 hover:bg-slate-100 transition"
          aria-label="Open mobile menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-base sm:text-lg md:text-xl font-bold text-slate-900 tracking-tight leading-tight">
            {getTitle()}
          </h1>
        </div>
        <span className="hidden sm:inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
          <ShieldCheck className="h-3 w-3 text-emerald-600" />
          Isolated Tenant
        </span>
      </div>

      {/* Global Search Bar (Medium & Large screens) */}
      <form onSubmit={handleSearchSubmit} className="hidden lg:flex relative w-80">
        <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Global search (leads, clients, msgs)..."
          className="w-full rounded-xl border border-slate-200 bg-slate-50/70 py-1.5 pl-9 pr-3 text-xs outline-none focus:border-indigo-500 focus:bg-white transition"
        />
      </form>

      {/* Right Top Bar Actions */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Mobile Search Button */}
        <button
          onClick={() => setShowSearchModal(true)}
          className="lg:hidden rounded-full p-2 text-slate-500 hover:bg-slate-100 transition"
          title="Search"
        >
          <Search className="h-5 w-5" />
        </button>

        {/* User Account Pill */}
        <div className="hidden sm:flex items-center gap-2 rounded-xl border border-slate-100 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="truncate max-w-[140px] md:max-w-[200px]">{user?.email}</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="relative rounded-full p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition"
            title="Notifications"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-indigo-600 px-1 text-[9px] font-bold text-white shadow-xs">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Popover */}
          {showDropdown && (
            <div className="absolute right-0 mt-2 w-80 max-w-[90vw] rounded-2xl bg-white p-4 shadow-2xl border border-slate-100 z-50 animate-in fade-in space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="font-bold text-xs text-slate-900">Notifications ({unreadCount} new)</span>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  >
                    <CheckCheck className="h-3 w-3" /> Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="text-center py-6 text-xs text-slate-400">
                    No notifications yet.
                  </div>
                ) : (
                  notifications.slice(0, 10).map((notif) => (
                    <div
                      key={notif.id}
                      onClick={() => handleNotificationClick(notif)}
                      className={`p-2.5 transition cursor-pointer rounded-lg ${
                        notif.is_read ? "hover:bg-slate-50 opacity-70" : "bg-indigo-50/50 hover:bg-indigo-50"
                      }`}
                    >
                      {notif.link_url ? (
                        <Link href={notif.link_url}>
                          <h4 className="font-bold text-xs text-slate-900">{notif.title}</h4>
                          <p className="text-[11px] text-slate-600 line-clamp-2 mt-0.5">{notif.message}</p>
                          <span className="text-[9px] text-slate-400 block mt-1">
                            {new Date(notif.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </Link>
                      ) : (
                        <div>
                          <h4 className="font-bold text-xs text-slate-900">{notif.title}</h4>
                          <p className="text-[11px] text-slate-600 line-clamp-2 mt-0.5">{notif.message}</p>
                          <span className="text-[9px] text-slate-400 block mt-1">
                            {new Date(notif.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Global Search Results Modal */}
      {showSearchModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-slate-900/60 p-4 pt-16 sm:pt-20 backdrop-blur-xs animate-in fade-in">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-5 sm:p-6 shadow-2xl border border-slate-100 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-sm">
                  Global Search
                </h3>
              </div>
              <button
                onClick={() => setShowSearchModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold p-1 rounded-lg hover:bg-slate-100 transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* In-Modal Search Input for Mobile */}
            <div className="relative">
              <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit(e)}
                placeholder="Search leads, clients, conversations..."
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-xs outline-none focus:border-indigo-500 focus:bg-white"
                autoFocus
              />
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {searching ? (
                <div className="text-center py-12 text-xs text-slate-400">
                  <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-indigo-500" />
                  Searching across tenant records...
                </div>
              ) : searchResults.length === 0 ? (
                <div className="text-center py-12 text-xs text-slate-400">
                  {searchQuery.trim() ? "No matching leads, clients, or conversations found." : "Type a query and press enter to search."}
                </div>
              ) : (
                searchResults.map((item) => (
                  <Link
                    key={`${item.entity_type}-${item.id}`}
                    href={item.url}
                    onClick={() => setShowSearchModal(false)}
                    className="block rounded-xl border border-slate-100 p-3 hover:bg-slate-50 transition space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {renderEntityIcon(item.entity_type)}
                        <h4 className="font-bold text-xs text-slate-900">{item.title}</h4>
                      </div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                        {item.entity_type}
                      </span>
                    </div>
                    {item.subtitle && (
                      <p className="text-[11px] font-medium text-slate-500">{item.subtitle}</p>
                    )}
                    {item.snippet && (
                      <p className="text-xs text-slate-600 line-clamp-2">{item.snippet}</p>
                    )}
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
