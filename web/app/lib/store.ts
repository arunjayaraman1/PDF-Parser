import { create } from "zustand";
import type { ParserRecommendation, PageResult, ParserRunMeta } from "./api";

interface AppState {
  description: string;
  setDescription: (desc: string) => void;

  file: File | null;
  fileId: string | null;
  filePath: string | null;
  setFile: (file: File | null, fileId?: string | null, filePath?: string | null) => void;

  recommendations: ParserRecommendation[];
  setRecommendations: (recs: ParserRecommendation[]) => void;

  selectedParsers: string[];
  setSelectedParsers: (parsers: string[]) => void;
  toggleParser: (parser: string) => void;

  parseResults: Record<string, PageResult[]>;
  setParseResults: (results: Record<string, PageResult[]>) => void;
  parserMeta: Record<string, ParserRunMeta>;
  setParserMeta: (meta: Record<string, ParserRunMeta>) => void;

  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  error: string | null;
  setError: (error: string | null) => void;

  currentPage: number;
  setCurrentPage: (page: number) => void;

  mineruProfile: "fast" | "quality" | "balanced" | null;
  setMineruProfile: (p: "fast" | "quality" | "balanced" | null) => void;

  activeTab: "parser" | "highlighter";
  setActiveTab: (tab: "parser" | "highlighter") => void;

  reset: () => void;
}

const initialState = {
  description: "",
  file: null,
  fileId: null,
  filePath: null,
  recommendations: [],
  selectedParsers: [],
  parseResults: {},
  parserMeta: {},
  isLoading: false,
  error: null,
  currentPage: 1,
  mineruProfile: null,
  activeTab: "parser" as const,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setDescription: (description) => set({ description }),

  setFile: (file, fileId = null, filePath = null) =>
    set({ file, fileId, filePath }),

  setRecommendations: (recommendations) => set({ recommendations }),

  setSelectedParsers: (selectedParsers) => set({ selectedParsers }),

  toggleParser: (parser) =>
    set((state) => {
      const isSelected = state.selectedParsers.includes(parser);
      const newParsers = isSelected
        ? state.selectedParsers.filter((p) => p !== parser)
        : [...state.selectedParsers, parser];
      return { selectedParsers: newParsers };
    }),

  setParseResults: (parseResults) => set({ parseResults }),
  setParserMeta: (parserMeta) => set({ parserMeta }),

  setIsLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  setCurrentPage: (currentPage) => set({ currentPage }),

  setMineruProfile: (mineruProfile) => set({ mineruProfile }),

  setActiveTab: (activeTab) => set({ activeTab }),

  reset: () => set(initialState),
}));