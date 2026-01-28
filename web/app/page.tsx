"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const LIVE_PRESTART_MS = 15 * 60 * 1000; // 15 min antes
const LIVE_POSTSTART_MS = (2 * 60 + 10) * 60 * 1000; // 2h10m después
// "Catch-up": si recargas mucho más tarde y el snapshot no está final, seguimos buscando FT un rato más.
const LIVE_CATCHUP_MS = 12 * 60 * 60 * 1000; // 12h después del inicio
const LIVE_POLL_MS = 5 * 60 * 1000; // cada 5 min


type Display = {
  league?: string;
  leagueLogo?: string;
  startTime?: string;
  home?: { name?: string; logo?: string };
  away?: { name?: string; logo?: string };
  live?: any;
};

type Pick = {
  sport?: string;
  eventId?: string | number;
  market?: string;
  selection?: string;
  odds?: number;
  ev?: number;
  premium?: boolean;
  risk?: { level?: string };
  display?: Display;
  p_estimated?: number;
  p_safe?: number;
};

type ParlayPremium = {
  type?: string;
  kind?: "SAFE_2" | "SAFE_4" | "BOOM_3" | string;
  label?: string;
  legs?: Pick[];
  combined_odds?: number;
  prob_parlay?: number;
  note?: string;
};

type Contract = {
  contract_date?: string;
  picks_classic?: any[];
  picks_parlay_premium?: ParlayPremium[];
  daily_featured_parlay?: ParlayPremium | null;
};

async function getContract(signal?: AbortSignal): Promise<Contract> {
  const res = await fetch(`${BACKEND_URL}/bets/today`, { cache: "no-store", signal });
  if (!res.ok) throw new Error(`No se pudo cargar (${res.status})`);
  return res.json();
}

async function getLiveEvents(sport: string, idsCsv: string, signal?: AbortSignal) {
  const qs = new URLSearchParams({ sport, ids: idsCsv }).toString();
  const res = await fetch(`${BACKEND_URL}/live/events?${qs}`, { cache: "no-store", signal });
  if (!res.ok) return null;
  return res.json();
}

function liveKey(sport?: string, eventId?: string | number) {
  const s = String(sport || "").trim().toLowerCase();
  const id = eventId === null || eventId === undefined ? "" : String(eventId).trim();
  if (!s || !id) return "";
  return `${s}:${id}`;
}



function asPickList(contract: Contract | null): Pick[] {
  const containers = contract?.picks_classic || [];
  const out: Pick[] = [];
  for (const c of containers) {
    if (Array.isArray(c)) out.push(...c);
    else if (c && typeof c === "object") out.push(c);
  }
  return out;
}

function n(x: any, fallback = NaN) {
  const v = Number(x);
  return Number.isFinite(v) ? v : fallback;
}

// DF_LIVE_UI_V1
function liveParts(live: any): { score: string | null; status: string | null } {
  if (!live || typeof live !== "object") return { score: null, status: null };
  const hs = (live as any).homeScore;
  const as_ = (live as any).awayScore;
  const hasScore = hs !== null && hs !== undefined && as_ !== null && as_ !== undefined;
  const score = hasScore ? `${hs}-${as_}` : null;

  const statusShort = (live as any).statusShort || (live as any).status || null;
  let time: string | null = null;
  const elapsed = Number((live as any).elapsed);
  if (Number.isFinite(elapsed)) time = `${elapsed}'`;
  else if ((live as any).timer) time = String((live as any).timer);
  // NOTE: NO usar `live.time` (suele venir como hora absoluta en UTC y descuadra con Europe/Madrid)

  const status = [statusShort, time].filter(Boolean).join(" ") || null;
  return { score, status };
}

function fmtLiveLine(live: any): string | null {
  const { score, status } = liveParts(live);
  if (!score && !status) return null;
  if (score && status) return `${score} · ${status}`;
  return score || status;
}

function liveMeta(live: any): { statusShort: string | null; time: string | null; hs: any; as: any } {
  if (!live || typeof live !== "object") return { statusShort: null, time: null, hs: null, as: null };
  const statusShort = (live as any).statusShort || (live as any).status || null;
  let time: string | null = null;
  const elapsed = Number((live as any).elapsed);
  if (Number.isFinite(elapsed)) time = `${elapsed}'`;
  else if ((live as any).timer) time = String((live as any).timer);
  // NOTE: NO usar `live.time` (suele venir como hora absoluta en UTC y descuadra con Europe/Madrid)
  return { statusShort, time, hs: (live as any).homeScore, as: (live as any).awayScore };
}

function isFinalStatus(ss?: string | null) {
    const v = String(ss || "").toUpperCase();
    return v === "FT" || v === "AET" || v === "PEN" || v === "FINAL";
  }

  function outcomeForPick(live: any, market?: string, selection?: string): "WIN" | "LOSE" | null {
    const { statusShort, hs, as } = liveMeta(live);
    if (!isFinalStatus(statusShort)) return null;

    const h = Number(hs);
    const a = Number(as);
    if (!Number.isFinite(h) || !Number.isFinite(a)) return null;

    const m = String(market || "").toLowerCase();
    if (!(m.includes("over/under") || m.includes("over under") || m.includes("total"))) return null;

    const sel = String(selection || "");
    const mm = sel.match(/\b(Over|Under)\s*([0-9]+(?:\.[0-9]+)?)/i);
    if (!mm) return null;

    const dir = String(mm[1]).toLowerCase();
    const line = Number(mm[2]);
    if (!Number.isFinite(line)) return null;

    const total = h + a;
    if (dir === "over") return total > line ? "WIN" : "LOSE";
    if (dir === "under") return total < line ? "WIN" : "LOSE";
    return null;
  }

  function borderStyleForOutcome(outcome: "WIN" | "LOSE" | null) {
    if (outcome === "WIN") return { borderColor: "rgba(34,197,94,0.55)", borderWidth: "2px" } as const;
    if (outcome === "LOSE") return { borderColor: "rgba(239,68,68,0.55)", borderWidth: "2px" } as const;
    return null;
  }

  function fmtOdds(x: any) {
  const v = n(x);
  if (!Number.isFinite(v)) return "—";
  return v.toFixed(2);
}

function fmtPct(x: any) {
  const v = n(x);
  if (!Number.isFinite(v)) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

function fmtEur(x: any) {
  const v = n(x);
  if (!Number.isFinite(v)) return "—";
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(v);
}

function fmtStart(iso?: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/Madrid",
  }).format(d);
}

function sportEs(s?: string) {
  const v = (s || "").toLowerCase();
  if (v === "football") return "Fútbol";
  if (v === "basketball") return "Baloncesto";
  if (v === "hockey") return "Hockey";
  if (v === "handball") return "Balonmano";
  if (v === "baseball") return "Béisbol";
  if (v === "volleyball") return "Voleibol";
  if (v === "rugby") return "Rugby";
  if (v === "nfl") return "NFL";
  if (v === "afl") return "AFL";
  return s || "—";
}

function selectionEs(sel?: string) {
  if (!sel) return "—";
  return sel.replace(/\bUnder\b/gi, "Menos de").replace(/\bOver\b/gi, "Más de");
}

function mercadoBonito(market?: string) {
  const v = (market || "").toLowerCase();
  if (v === "over/under") return "Total (Más/Menos)";
  if (v === "moneyline") return "Ganador";
  if (v === "handicap") return "Hándicap";
  if (v === "home/away") return "Local/Visitante";
  if (v === "3way result") return "1X2 (3 opciones)";
  if (v.includes("asian handicap")) return "Hándicap asiático";
  if (v.includes("total - home")) return "Total del local";
  if (v.includes("total - away")) return "Total del visitante";
  return market || "Mercado";
}

function confianzaBadge(ps?: number) {
  if (ps === null || ps === undefined) return null;
  const p = Number(ps);
  if (!Number.isFinite(p)) return null;

  const pct = Math.round(p * 100);
  const cls = pct >= 75 ? "badge badge-good" : pct >= 60 ? "badge badge-warn" : "badge badge-bad";

  return (
    <span className="relative inline-flex items-center group">
      <span className={cls} tabIndex={0} role="button" aria-label="Confianza (toca para ver explicación)">
        Confianza {pct}%
      </span>
      <span className="absolute left-0 bottom-full mb-2 z-50 hidden w-72 rounded-lg border border-white/10 bg-black/90 p-3 text-xs text-white/90 shadow-lg group-hover:block group-focus-within:block">
        Confianza = probabilidad estimada por el modelo. No garantiza acierto; solo indica qué tan probable es según datos y mercado.
      </span>
    </span>
  );
}

function parlayTag(kind?: string) {
  if (kind === "BOOM_3") return "BOOM";
  return "SEGURO";
}

function initialsFromAlt(alt: string) {
  const cleaned = (alt || "").split("(")[0].trim();
  const parts = cleaned.split(" ").filter(Boolean);
  const a = (parts[0]?.[0] || "").toUpperCase();
  const b = (parts[1]?.[0] || "").toUpperCase();
  return (a + b) || "—";
}

function isBadLogo(src?: string | null) {
  if (!src) return true;
  const s = String(src).trim();
  if (!s) return true;
  const low = s.toLowerCase();
  if (low === "null" || low === "none" || low === "n/a" || low === "na" || low === "—") return true;
  return false;
}

function ImgTeam({
  src,
  alt,
  size = 40,
  className = "",
}: {
  src?: string | null;
  alt: string;
  size?: number;
  className?: string;
}) {
  const [ok, setOk] = useState(true);

  if (isBadLogo(src) || !ok) {
    const initials = initialsFromAlt(alt);
    return (
      <div
        aria-label={alt}
        title={alt}
        style={{ width: size, height: size }}
        className={`rounded-xl border border-white/10 bg-gradient-to-br from-white/20 via-white/10 to-white/5 flex items-center justify-center text-[11px] font-semibold tracking-wide text-white/75 select-none ${className}`}
      >
        {initials}
      </div>
    );
  }

  // eslint-disable-next-line @next/next/no-img-element
  return (
    <img
      src={src as any}
      alt={alt}
      style={{ width: size, height: size }}
      className={`rounded-xl bg-white/5 border border-white/10 object-contain ${className}`}
      referrerPolicy="no-referrer"
        loading="lazy"
        decoding="async"
        onLoad={(e) => {
          const img = e.currentTarget as HTMLImageElement;
          if (!img?.naturalWidth || img.naturalWidth <= 1) setOk(false);
        }}
        onError={() => setOk(false)}
    />
  );
}

function InfoTip({ children, tip }: { children: React.ReactNode; tip: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-flex items-center group">
      <span
        tabIndex={0}
        role="button"
        aria-label="Info"
        className="cursor-help"
        onClick={(e) => {
          e.preventDefault();
          setOpen((v) => !v);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen((v) => !v);
          }
          if (e.key === "Escape") setOpen(false);
        }}
        onBlur={() => setOpen(false)}
      >
        {children}
      </span>

      <span
        className={
          "absolute left-0 bottom-full mb-2 z-50 w-80 rounded-lg border border-white/10 bg-black/90 p-3 text-xs text-white/90 shadow-lg transition-opacity " +
          (open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none") +
          " group-hover:opacity-100 group-hover:pointer-events-auto group-focus-within:opacity-100 group-focus-within:pointer-events-auto"
        }
      >
        {tip}
      </span>
    </span>
  );
}

function LiveScoreMini({
  live,
  home,
  away,
  size = 46,
}: {
  live: any;
  home?: { name?: string; logo?: string };
  away?: { name?: string; logo?: string };
  size?: number;
}) {
  const { statusShort, time, hs, as } = liveMeta(live);
  const hasScore = hs !== null && hs !== undefined && as !== null && as !== undefined;
  const showStatus = Boolean(statusShort || time);

  return (
    <div className="flex items-center gap-3">
      <div className="flex flex-col items-center">
        <ImgTeam src={home?.logo} alt={home?.name || "Local"} size={size} />
        <div className="mt-1 text-[15px] font-semibold tabular-nums text-slate-100">{hasScore ? String(hs) : "—"}</div>
      </div>

      <div className="flex flex-col items-center justify-center min-w-14">
        {showStatus ? (
          <>
            <div className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[11px] text-slate-100/90">
              {statusShort || "—"}
            </div>
            {time ? <div className="mt-0.5 text-[11px] text-slate-300/80 tabular-nums">{time}</div> : null}
          </>
        ) : (
          <div className="subtle text-[11px]">—</div>
        )}
      </div>

      <div className="flex flex-col items-center">
        <ImgTeam src={away?.logo} alt={away?.name || "Visitante"} size={size} />
        <div className="mt-1 text-[15px] font-semibold tabular-nums text-slate-100">{hasScore ? String(as) : "—"}</div>
      </div>
    </div>
  );
}

export default function Page() {
  const [contract, setContract] = useState<Contract | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<"classic" | "parley" | "history" | "soccer" | "rugby" | "nfl" | "basketball" | "hockey" | "afl" | "tennis" | "baseball">("classic");
  const [stake, setStake] = useState<number>(50);
  const [liveOverrideByKey, setLiveOverrideByKey] = useState<Record<string, any>>({});
  const [historyDays, setHistoryDays] = useState<any[]>([]);
  const [selectedHistoryDay, setSelectedHistoryDay] = useState<string | null>(null);
  const [historyDayData, setHistoryDayData] = useState<any | null>(null);
  const liveRef = useRef<Record<string, any>>({});

  useEffect(() => {
    const ctrl = new AbortController();
    getContract(ctrl.signal)
      .then(setContract)
      .catch((e: any) => setErr(e?.message || String(e)));
    return () => ctrl.abort();
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch(`${BACKEND_URL}/history/days?limit=30`, { cache: "no-store", signal: ctrl.signal })
      .then((res) => res.json())
      .then((data) => setHistoryDays(data.days || []))
      .catch(() => {
        /* silent fail */
      });
    return () => ctrl.abort();
  }, []);

  useEffect(() => {
    if (!selectedHistoryDay) {
      setHistoryDayData(null);
      return;
    }
    const ctrl = new AbortController();
    fetch(`${BACKEND_URL}/history/${selectedHistoryDay}`, { cache: "no-store", signal: ctrl.signal })
      .then((res) => res.json())
      .then(setHistoryDayData)
      .catch(() => {
        setHistoryDayData(null);
      });
    return () => ctrl.abort();
  }, [selectedHistoryDay]);

  useEffect(() => {
    liveRef.current = liveOverrideByKey;
  }, [liveOverrideByKey]);

  // Live polling (READ-ONLY): 1 request por deporte cada tick (ids deduplicados)
  useEffect(() => {
    if (!contract) return;
    const ctrl = new AbortController();
    let stopped = false;

    const tick = async () => {
      if (stopped) return;
      const now = Date.now();

      const byK = new Map<string, { sport: string; id: string; startMs: number | null; snapshotLive: any }>();

      const addPick = (p: any) => {
        if (!p) return;
        const sport = String(p.sport || "").trim().toLowerCase();
        const id = p.eventId === null || p.eventId === undefined ? "" : String(p.eventId).trim();
        if (!sport || !id) return;

        const d: any = p.display || {};
        const startTime = d?.startTime;
        const startMsRaw = startTime ? new Date(startTime).getTime() : Number.NaN;
        const startMs = Number.isFinite(startMsRaw) ? startMsRaw : null;
        const snapshotLive = d?.live;

        const k = `${sport}:${id}`;
        const prev = byK.get(k);
        if (!prev) {
          byK.set(k, { sport, id, startMs, snapshotLive });
          return;
        }
        if (prev.startMs === null) prev.startMs = startMs;
        else if (startMs !== null) prev.startMs = Math.min(prev.startMs, startMs);
        if (!prev.snapshotLive && snapshotLive) prev.snapshotLive = snapshotLive;
      };

      // classic
      for (const p of asPickList(contract)) addPick(p);

      // parlays premium
      const pp = Array.isArray(contract.picks_parlay_premium) ? contract.picks_parlay_premium : [];
      for (const par of pp) for (const leg of (par?.legs || [])) addPick(leg);

      // featured parlay (si existe)
      const fp: any = (contract as any).daily_featured_parlay;
      if (fp && typeof fp === "object") for (const leg of (fp?.legs || [])) addPick(leg);

      const activeIdsBySport = new Map<string, Set<string>>();

      for (const ev of byK.values()) {
        if (ev.startMs === null) continue;
        const withinStandard = now >= ev.startMs - LIVE_PRESTART_MS && now <= ev.startMs + LIVE_POSTSTART_MS;
        const withinCatchup = now > ev.startMs + LIVE_POSTSTART_MS && now <= ev.startMs + LIVE_CATCHUP_MS;
        const within = withinStandard || withinCatchup;
        if (!within) continue;

        const kk = `${ev.sport}:${ev.id}`;
        const liveFinal = (liveRef.current as any)[kk] ?? ev.snapshotLive;
        const { statusShort } = liveMeta(liveFinal);
        if (isFinalStatus(statusShort)) continue;

        if (!activeIdsBySport.has(ev.sport)) activeIdsBySport.set(ev.sport, new Set());
        activeIdsBySport.get(ev.sport)!.add(ev.id);
      }

      for (const [sport, idSet] of activeIdsBySport.entries()) {
        const idsCsv = Array.from(idSet).join(",");
        if (!idsCsv) continue;
        try {
          const data = await getLiveEvents(sport, idsCsv, ctrl.signal);
          const liveById = data?.live_by_id;
          if (!liveById || typeof liveById !== "object") continue;
          setLiveOverrideByKey((prev) => {
            const next = { ...prev };
            for (const [id, live] of Object.entries(liveById)) {
              (next as any)[`${sport}:${String(id)}`] = live;
            }
            return next;
          });
        } catch {
          // silent: UI falls back to snapshot
        }
      }
    };

    tick();
    const t = setInterval(tick, LIVE_POLL_MS);
    return () => {
      stopped = true;
      clearInterval(t);
      ctrl.abort();
    };
  }, [contract]);


  const classic = useMemo(() => {
    const raw = asPickList(contract);
    // Top 10 picks de TODOS los deportes, ordenados por confianza
    return raw.slice().sort((a, b) => n(b.p_safe, -1e9) - n(a.p_safe, -1e9)).slice(0, 10);
  }, [contract]);

  // Picks agrupados por deporte
  const picksBySport = useMemo(() => {
    const raw = asPickList(contract);
    const byS: Record<string, Pick[]> = {};
    for (const p of raw) {
      const s = (p.sport || "other").toLowerCase();
      if (!byS[s]) byS[s] = [];
      byS[s].push(p);
    }
    // Ordenar cada deporte por p_safe
    for (const s in byS) {
      byS[s].sort((a, b) => n(b.p_safe, -1e9) - n(a.p_safe, -1e9));
    }
    return byS;
  }, [contract]);

  const parlays = useMemo(() => {
    const arr = Array.isArray(contract?.picks_parlay_premium) ? (contract!.picks_parlay_premium as ParlayPremium[]) : [];
    return arr.slice().sort((a, b) => {
      const ka = a.kind === "BOOM_3" ? 0 : 1;
      const kb = b.kind === "BOOM_3" ? 0 : 1;
      if (ka !== kb) return ka - kb;
      return n(b.combined_odds, -1e9) - n(a.combined_odds, -1e9);
    });
  }, [contract]);

  if (err) {
    return (
      <main className="space-y-6">
        <section className="card">
          <div className="card-inner p-6 overflow-visible">
            <div className="h1">ULTIMATE PREDICTOR</div>
            <div className="subtle mt-2">No se pudo cargar la página.</div>
            <pre className="mt-3 text-sm text-red-200 whitespace-pre-wrap">{err}</pre>
          </div>
        </section>
      </main>
    );
  }

  if (!contract) {
    return (
      <main className="space-y-6">
        <section className="card">
          <div className="card-inner p-6 overflow-visible">
            <div className="h1">ULTIMATE PREDICTOR</div>
            <div className="subtle mt-2">Cargando…</div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      {/* Banner */}
      <section className="card">
        <div
          className="card-inner p-6 md:p-8 overflow-visible"
          style={{
            background:
              "radial-gradient(1200px 240px at 15% 10%, rgba(17,197,167,0.18), transparent 55%), radial-gradient(900px 240px at 85% 0%, rgba(29,139,255,0.18), transparent 55%)",
          }}
        >
          <div className="flex flex-col gap-4">
            <div>
              <div className="h1">ULTIMATE PREDICTOR</div>
              <div className="subtle mt-2">Jugadas claras. Decisiones inteligentes.</div>
            </div>

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="flex items-center gap-2 flex-wrap">
                <button className={tab === "classic" ? "badge badge-accent" : "badge"} onClick={() => setTab("classic")}>
                  Classic (Top 10)
                </button>
                <button className={tab === "parley" ? "badge badge-accent" : "badge"} onClick={() => setTab("parley")}>
                  Parley
                </button>
                
                {/* Sport tabs - muestra solo deportes con picks */}
                {Object.keys(picksBySport).filter(s => picksBySport[s].length > 0).map((sport) => (
                  <button 
                    key={sport}
                    className={tab === sport ? "badge badge-accent" : "badge"} 
                    onClick={() => setTab(sport as any)}
                  >
                    {sport.charAt(0).toUpperCase() + sport.slice(1)} ({picksBySport[sport].length})
                  </button>
                ))}
                
                <button className={tab === "history" ? "badge badge-accent" : "badge"} onClick={() => { setTab("history"); setSelectedHistoryDay(null); }}>
                  Historial
                </button>
              </div>

              <div className="flex items-center gap-3">
                <div className="mono">Stake (€)</div>
                <input
                  className="h-10 w-28 rounded-xl border border-white/10 bg-white/[0.04] px-3 text-slate-100 outline-none focus:border-white/20"
                  type="number"
                  min={1}
                  step={1}
                  value={Number.isFinite(stake) ? stake : 50}
                  onChange={(e) => setStake(Number(e.target.value || 0))}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CLASSIC */}
      {tab === "classic" && (
        <>
          {!classic.length ? (
            <section className="card">
              <div className="card-inner p-6 text-slate-300/80 overflow-visible">Hoy no hay predicciones.</div>
            </section>
          ) : (
            <section className="grid gap-4 md:grid-cols-2">
              {classic.map((p, idx) => {
                const d = p.display || {};
                const home = d.home || {};
                const away = d.away || {};
                const profit = stake * (n(p.odds, NaN) - 1);
                const k = liveKey(p.sport, p.eventId);
                const liveFinal = k ? (liveOverrideByKey[k] ?? (d as any).live) : (d as any).live;
                const outcome = outcomeForPick(liveFinal, p.market, p.selection);

                return (
                  <article key={`${p.sport || "sport"}-${p.eventId || "event"}-${idx}`} className="card" style={{ overflow: "visible", ...(borderStyleForOutcome(outcome) || {}) }}>
                    <div className="card-inner p-5 overflow-visible">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="badge badge-accent">{sportEs(p.sport)}</span>
                            {d.league ? <span className="badge">{d.league}</span> : null}
                            {confianzaBadge(p?.p_safe)}
                          </div>

                          <div className="mt-2 text-lg font-semibold tracking-tight truncate">
                            {home?.name || "Local"} <span className="text-slate-300/70">vs</span> {away?.name || "Visitante"}
                          </div>

                          <div className="subtle text-xs mt-1">Empieza: {fmtStart(d.startTime)}</div>
                        </div>

                          <div className="shrink-0">
                            <LiveScoreMini live={liveFinal} home={home} away={away} size={48} />
                          </div>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-3">
                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 col-span-2">
                          <div className="mono">Mercado</div>
                          <div className="text-sm text-slate-100">{mercadoBonito(p.market)}</div>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 col-span-2">
                          <div className="mono">Selecciona</div>
                          <div className="text-sm text-slate-100">{selectionEs(p.selection)}</div>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                          <div className="mono">Cuota</div>
                          <div className="text-sm text-slate-100">{fmtOdds(p.odds)}</div>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                          <div className="mono">Ganancia potencial</div>
                          <div className="text-sm text-slate-100">{fmtEur(profit)}</div>
                        </div>

                        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 col-span-2">
                          <div className="mono">Retorno total</div>
                          <div className="text-sm text-slate-100">{fmtEur(stake * n(p.odds, NaN))}</div>
                        </div>
                      </div>

                      {Number.isFinite(n(p.p_safe, NaN)) ? (
                        <div className="subtle text-xs mt-3">
                          <InfoTip
                            tip={
                              <>
                                <div className="font-semibold text-white/90">¿Qué significa esta probabilidad?</div>
                                <div className="mt-1">
                                  Es la <span className="text-white">estimación del modelo</span> para esta selección. No garantiza acierto; solo
                                  indica qué tan probable es según datos y mercado.
                                </div>
                              </>
                            }
                          >
                            <span>
                              Prob. estimada: <span className="text-slate-100">{fmtPct(p.p_safe)}</span>
                            </span>
                          </InfoTip>
                        </div>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </section>
          )}
        </>
      )}

      {/* SPORT TABS - DYNAMIC RENDERING */}
      {Object.keys(picksBySport)
        .filter((s) => picksBySport[s].length > 0)
        .map((sport) =>
          tab === sport ? (
            <div key={sport}>
              {!picksBySport[sport].length ? (
                <section className="card">
                  <div className="card-inner p-6 text-slate-300/80 overflow-visible">No hay predicciones para {sportEs(sport)}.</div>
                </section>
              ) : (
                <section className="grid gap-4 md:grid-cols-2">
                  {picksBySport[sport].map((p, idx) => {
                    const d = p.display || {};
                    const home = d.home || {};
                    const away = d.away || {};
                    const profit = stake * (n(p.odds, NaN) - 1);
                    const k = liveKey(p.sport, p.eventId);
                    const liveFinal = k ? (liveOverrideByKey[k] ?? (d as any).live) : (d as any).live;
                    const outcome = outcomeForPick(liveFinal, p.market, p.selection);

                    return (
                      <article key={`${p.sport || "sport"}-${p.eventId || "event"}-${idx}`} className="card" style={{ overflow: "visible", ...(borderStyleForOutcome(outcome) || {}) }}>
                        <div className="card-inner p-5 overflow-visible">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="badge badge-accent">{sportEs(p.sport)}</span>
                                {d.league ? <span className="badge">{d.league}</span> : null}
                                {confianzaBadge(p?.p_safe)}
                              </div>

                              <div className="mt-2 text-lg font-semibold tracking-tight truncate">
                                {home?.name || "Local"} <span className="text-slate-300/70">vs</span> {away?.name || "Visitante"}
                              </div>

                              <div className="subtle text-xs mt-1">Empieza: {fmtStart(d.startTime)}</div>
                            </div>

                            <div className="shrink-0">
                              <LiveScoreMini live={liveFinal} home={home} away={away} size={48} />
                            </div>
                          </div>

                          <div className="mt-4 grid grid-cols-2 gap-3">
                            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 col-span-2">
                              <div className="mono">Mercado</div>
                              <div className="text-sm text-slate-100">{mercadoBonito(p.market)}</div>
                            </div>

                            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 col-span-2">
                              <div className="mono">Selecciona</div>
                              <div className="text-sm text-slate-100">{selectionEs(p.selection)}</div>
                            </div>

                            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                              <div className="mono">Cuota</div>
                              <div className="text-sm text-slate-100">{fmtOdds(p.odds)}</div>
                            </div>

                            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                              <div className="mono">Ganancia potencial</div>
                              <div className="text-sm text-slate-100">{fmtEur(profit)}</div>
                            </div>

                            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 col-span-2">
                              <div className="mono">Retorno total</div>
                              <div className="text-sm text-slate-100">{fmtEur(stake * n(p.odds, NaN))}</div>
                            </div>
                          </div>

                          {Number.isFinite(n(p.p_safe, NaN)) ? (
                            <div className="subtle text-xs mt-3">
                              <InfoTip
                                tip={
                                  <>
                                    <div className="font-semibold text-white/90">¿Qué significa esta probabilidad?</div>
                                    <div className="mt-1">
                                      Es la <span className="text-white">estimación del modelo</span> para esta selección. No garantiza acierto; solo
                                      indica qué tan probable es según datos y mercado.
                                    </div>
                                  </>
                                }
                              >
                                <span>
                                  Prob. estimada: <span className="text-slate-100">{fmtPct(p.p_safe)}</span>
                                </span>
                              </InfoTip>
                            </div>
                          ) : null}
                        </div>
                      </article>
                    );
                  })}
                </section>
              )}
            </div>
          ) : null
        )}

      {/* PARLEY */}
      {tab === "parley" && (
        <>
          {!parlays.length ? (
            <section className="card">
              <div className="card-inner p-6 overflow-visible">
                <div className="h1">Parleys</div>
                <div className="subtle mt-2">Hoy no hay parleys.</div>
              </div>
            </section>
          ) : (
            <section className="grid gap-4 md:grid-cols-2">
              {parlays.map((p, idx) => {
                const legs = Array.isArray(p.legs) ? p.legs : [];
                const title = `${legs.length} Selecciones`;
                const tag = parlayTag(p.kind);

                const profit = stake * (n(p.combined_odds, NaN) - 1);
                const totalReturn = stake * n(p.combined_odds, NaN);

                const note = typeof p.note === "string" ? p.note.trim() : "";
                const showNote = Boolean(note) && !note.toLowerCase().startsWith("fallback:");

                  const parlayOutcome = (() => {
                    const outs = legs.map((leg) => {
                      const dd: any = (leg as any).display || {};
                      const kk = liveKey(leg.sport, leg.eventId);
                      const liveFinalLeg = kk ? (liveOverrideByKey[kk] ?? (dd as any).live) : (dd as any).live;
                      return outcomeForPick(liveFinalLeg, leg.market, leg.selection);
                    });
                    if (!outs.length) return null;
                    if (outs.some((o) => o === null)) return null;
                    if (outs.some((o) => o === "LOSE")) return "LOSE";
                    return "WIN";
                  })();


                return (
                  <article key={`${p.kind || "parley"}-${idx}`} className="card" style={{ overflow: "visible", ...(borderStyleForOutcome(parlayOutcome) || {}) }}>
                    <div className="card-inner p-5 overflow-visible">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={p.kind === "BOOM_3" ? "badge badge-accent" : "badge"}>{tag}</span>
                          </div>

                          <div className="mt-2 text-lg font-semibold tracking-tight">{title}</div>

                          <div className="subtle text-xs mt-1">
                            Cuota combinada: <span className="text-slate-100">{fmtOdds(p.combined_odds)}</span> ·{" "}
                            <InfoTip
                              tip={
                                <>
                                  <div className="font-semibold text-white/90">¿Por qué es tan baja?</div>
                                  <div className="mt-1">
                                    Imagina que es como pasar <span className="text-white">varias pruebas seguidas</span>.
                                  </div>
                                  <div className="mt-1">
                                    Si fallas una, el parlay falla. Por eso, al juntar varias selecciones, el % baja mucho.
                                  </div>
                                </>
                              }
                            >
                              <span>
                                Prob. est.: <span className="text-slate-100">{fmtPct(p.prob_parlay)}</span>
                              </span>
                            </InfoTip>
                          </div>

                          <div className="subtle text-xs mt-1">
                            Retorno total (con stake {fmtEur(stake)}): <span className="text-slate-100">{fmtEur(totalReturn)}</span>
                            {" · "}
                            Ganancia potencial: <span className="text-slate-100">{fmtEur(profit)}</span>
                          </div>

                          {showNote ? <div className="subtle text-xs mt-1">{note}</div> : null}
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3">
                        {legs.map((leg, i) => {
                          const dd = leg.display || {};
                          const h = dd.home || {};
                          const a = dd.away || {};
                          const hasTeams = Boolean(h.name || a.name);
                          const kk = liveKey(leg.sport, leg.eventId);
                          const liveFinalLeg = kk ? (liveOverrideByKey[kk] ?? (dd as any).live) : (dd as any).live;
                          const outcome = outcomeForPick(liveFinalLeg, leg.market, leg.selection);

                          return (
                            <div key={i} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3" style={{ ...(borderStyleForOutcome(outcome) || {}) }}>
                              <div className="mono">Selección {i + 1}</div>

                              <div className="mt-1 flex flex-nowrap items-start justify-between gap-3">
                                <div className="min-w-0">
                                  <div className="text-sm text-slate-100">
                                    {hasTeams ? (
                                      <span className="truncate block">
                                        {h.name || "Local"} <span className="text-slate-300/70">vs</span> {a.name || "Visitante"}
                                      </span>
                                    ) : (
                                      <span className="truncate block">
                                        {sportEs(leg.sport)} · Evento {String(leg.eventId || "—")}
                                      </span>
                                    )}
                                  </div>

                                  <div className="subtle text-xs mt-1">
                                    {sportEs((dd as any).sport || leg.sport)} · {(dd as any).league || "—"}
                                  </div>

                                  <div className="subtle text-xs mt-1">
                                    {mercadoBonito(leg.market)} · <span className="text-slate-100">{selectionEs(leg.selection)}</span> · Cuota{" "}
                                    <span className="text-slate-100">{fmtOdds(leg.odds)}</span>
                                  </div>
                                </div>

                                  {hasTeams ? (
                                    <div className="shrink-0">
                                      <LiveScoreMini live={liveFinalLeg} home={h} away={a} size={48} />
                                    </div>
                                  ) : null}
                                </div>
                              </div>
                            );
                        })}
                      </div>
                    </div>
                  </article>
                );
              })}
            </section>
          )}
        </>
      )}

      {/* HISTORIAL */}
      {tab === "history" && (
        <>
          {!selectedHistoryDay ? (
            <section className="grid gap-4 md:grid-cols-2">
              {historyDays.length === 0 ? (
                <section className="card md:col-span-2">
                  <div className="card-inner p-6 overflow-visible">
                    <div className="h2">Historial</div>
                    <div className="subtle mt-2">No hay historial disponible.</div>
                  </div>
                </section>
              ) : (
                historyDays.map((day) => (
                  <article key={day.day} className="card" style={{ cursor: "pointer" }} onClick={() => setSelectedHistoryDay(day.day)}>
                    <div className="card-inner p-5 overflow-visible hover:bg-white/[0.06] transition-colors">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-lg font-semibold tracking-tight">{day.day}</div>
                          <div className="subtle text-xs mt-2">
                            Archivado: {new Date(day.archived_at).toLocaleString("es-ES", { timeZone: "Europe/Madrid" })}
                          </div>
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-2">
                        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2">
                          <div className="mono text-xs">Clásicas</div>
                          <div className="text-sm text-slate-100 mt-1">
                            {day.classic_wins}/{day.classic_total} ✓
                          </div>
                        </div>
                        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2">
                          <div className="mono text-xs">Parlays</div>
                          <div className="text-sm text-slate-100 mt-1">
                            {day.parlay_wins}/{day.parlay_total} ✓
                          </div>
                        </div>
                      </div>
                    </div>
                  </article>
                ))
              )}
            </section>
          ) : historyDayData ? (
            <>
              <section className="card">
                <div className="card-inner p-6 overflow-visible">
                  <button
                    className="badge"
                    onClick={() => {
                      setSelectedHistoryDay(null);
                      setHistoryDayData(null);
                    }}
                  >
                    ← Volver
                  </button>
                  <div className="h2 mt-3">{selectedHistoryDay}</div>
                  <div className="subtle text-xs mt-2">
                    Archivado: {new Date(historyDayData.archived_at).toLocaleString("es-ES", { timeZone: "Europe/Madrid" })}
                  </div>
                </div>
              </section>

              {/* Clásicas del histórico */}
              {Array.isArray(historyDayData.picks_classic) && historyDayData.picks_classic.length > 0 && (
                <section>
                  <div className="h2 mb-4">Apuestas Clásicas</div>
                  <section className="grid gap-4 md:grid-cols-2">
                    {(historyDayData.picks_classic as any[]).map((p, idx) => {
                      const d = p.display || {};
                      const outcome = p.outcome;
                      return (
                        <article key={idx} className="card" style={{ overflow: "visible", ...(borderStyleForOutcome(outcome as any) || {}) }}>
                          <div className="card-inner p-5 overflow-visible">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="badge badge-accent">{sportEs(p.sport)}</span>
                                  {outcome === "WIN" && <span className="badge" style={{ borderColor: "rgba(34,197,94,0.55)" }}>✓ WIN</span>}
                                  {outcome === "LOSE" && <span className="badge" style={{ borderColor: "rgba(239,68,68,0.55)" }}>✗ LOSE</span>}
                                  {outcome === "PENDING" && <span className="badge">⏳ PENDING</span>}
                                </div>
                                <div className="mt-2 text-sm font-semibold truncate">
                                  {d.home?.name || "Local"} vs {d.away?.name || "Visitante"}
                                </div>
                                <div className="subtle text-xs mt-1">{fmtStart(d.startTime)}</div>
                                <div className="subtle text-xs mt-1">{mercadoBonito(p.market)}</div>
                              </div>
                            </div>
                            <div className="mt-3 grid grid-cols-2 gap-2">
                              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2">
                                <div className="mono text-xs">Cuota</div>
                                <div className="text-sm text-slate-100">{fmtOdds(p.odds)}</div>
                              </div>
                              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2">
                                <div className="mono text-xs">Selección</div>
                                <div className="text-xs text-slate-100">{selectionEs(p.selection)}</div>
                              </div>
                            </div>
                          </div>
                        </article>
                      );
                    })}
                  </section>
                </section>
              )}

              {/* Parlays del histórico */}
              {Array.isArray(historyDayData.picks_parlay_premium) && historyDayData.picks_parlay_premium.length > 0 && (
                <section className="mt-6">
                  <div className="h2 mb-4">Parlays</div>
                  <section className="grid gap-4 md:grid-cols-2">
                    {(historyDayData.picks_parlay_premium as any[]).map((p, idx) => {
                      const outcome = p.outcome;
                      const legs = p.legs || [];
                      return (
                        <article key={idx} className="card" style={{ overflow: "visible", ...(borderStyleForOutcome(outcome as any) || {}) }}>
                          <div className="card-inner p-5 overflow-visible">
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className={p.kind === "BOOM_3" ? "badge badge-accent" : "badge"}>{parlayTag(p.kind)}</span>
                                  {outcome === "WIN" && <span className="badge" style={{ borderColor: "rgba(34,197,94,0.55)" }}>✓ WIN</span>}
                                  {outcome === "LOSE" && <span className="badge" style={{ borderColor: "rgba(239,68,68,0.55)" }}>✗ LOSE</span>}
                                  {outcome === "PENDING" && <span className="badge">⏳ PENDING</span>}
                                </div>
                                <div className="mt-2 text-sm font-semibold">{legs.length} Selecciones</div>
                                <div className="subtle text-xs mt-1">Cuota: {fmtOdds(p.combined_odds)}</div>
                              </div>
                            </div>
                            <div className="mt-3 space-y-2">
                              {legs.map((leg: any, i: number) => (
                                <div key={i} className="rounded-lg border border-white/10 bg-white/[0.02] p-2">
                                  <div className="flex items-center justify-between gap-2">
                                    <div className="min-w-0 flex-1">
                                      <div className="text-xs text-slate-100 truncate">Sel. {i + 1}</div>
                                      <div className="text-xs text-slate-300/70 truncate">{selectionEs(leg.selection)}</div>
                                    </div>
                                    <div className="shrink-0 text-xs">
                                      {p.leg_outcomes?.[i] === "WIN" && <span style={{ color: "rgba(34,197,94,1)" }}>✓</span>}
                                      {p.leg_outcomes?.[i] === "LOSE" && <span style={{ color: "rgba(239,68,68,1)" }}>✗</span>}
                                      {p.leg_outcomes?.[i] === "PENDING" && <span>⏳</span>}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </article>
                      );
                    })}
                  </section>
                </section>
              )}
            </>
          ) : (
            <section className="card">
              <div className="card-inner p-6 overflow-visible">
                <div className="subtle">Cargando historial...</div>
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}
