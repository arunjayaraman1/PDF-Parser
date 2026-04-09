"use client";

import { ReactNode } from "react";
import { cn } from "../lib/utils";

interface ColumnProps {
  title: string;
  pageCount: number;
  icon?: ReactNode;
  accentColor?: "cyan" | "indigo" | "emerald" | "amber" | "rose";
  children: ReactNode;
  className?: string;
}

const colorMap = {
  cyan: {
    headerBg: "from-cyan-500/20 to-blue-500/20",
    headerBorder: "border-cyan-500/30",
    iconBg: "bg-cyan-500/20",
    iconColor: "text-cyan-400",
  },
  indigo: {
    headerBg: "from-indigo-500/20 to-purple-500/20",
    headerBorder: "border-indigo-500/30",
    iconBg: "bg-indigo-500/20",
    iconColor: "text-indigo-400",
  },
  emerald: {
    headerBg: "from-emerald-500/20 to-teal-500/20",
    headerBorder: "border-emerald-500/30",
    iconBg: "bg-emerald-500/20",
    iconColor: "text-emerald-400",
  },
  amber: {
    headerBg: "from-amber-500/20 to-orange-500/20",
    headerBorder: "border-amber-500/30",
    iconBg: "bg-amber-500/20",
    iconColor: "text-amber-400",
  },
  rose: {
    headerBg: "from-rose-500/20 to-pink-500/20",
    headerBorder: "border-rose-500/30",
    iconBg: "bg-rose-500/20",
    iconColor: "text-rose-400",
  },
};

export function Column({ title, pageCount, icon, accentColor = "cyan", children, className }: ColumnProps) {
  const colors = colorMap[accentColor];

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div
        className={cn(
          "flex items-center justify-between px-4 py-3 rounded-t-2xl",
          "bg-gradient-to-r",
          colors.headerBg,
          "border border-b-0",
          colors.headerBorder
        )}
      >
        <div className="flex items-center gap-2.5">
          {icon && (
            <div className={cn("p-1.5 rounded-lg", colors.iconBg)}>
              <div className={colors.iconColor}>{icon}</div>
            </div>
          )}
          <span className="text-sm font-semibold text-zinc-200">{title}</span>
        </div>
        <span className="text-xs text-zinc-500 bg-zinc-800/50 px-2.5 py-1 rounded-md font-medium">
          {pageCount} {pageCount === 1 ? "page" : "pages"}
        </span>
      </div>
      <div
        className={cn(
          "flex-1 overflow-auto rounded-b-2xl",
          "bg-zinc-900/40 border border-zinc-800/40",
          "scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent"
        )}
      >
        {children}
      </div>
    </div>
  );
}