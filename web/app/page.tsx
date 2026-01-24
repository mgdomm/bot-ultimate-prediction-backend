"use client";

import React, { useEffect, useMemo, useState } from "react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

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
  else if ((live as any).time) time = String((live as any).time);

  const status = [statusShort, time].filter(Boolean).join(" ") || null;
  return { score, status };
}

function fmtLiveLine(live: any): string | null {
  const { score, status } = liveParts(live);
  if (!score && !status) return null;
  if (score && status) return `${score} · ${status}`;
  return score || status;
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
        <span className="absolute left-0 top-full mt-2 z-50 hidden w-72 rounded-lg border border-white/10 bg-black/90 p-3 text-xs text-white/90 shadow-lg group-hover:block group-focus-within:block">
          Confianza = probabilidad estimada por el modelo. No garantiza acierto; solo indica qué tan probable es según datos y mercado.
        </span>
      </span>
    );
  }

function cleanParlayTitle(label?: string, kind?: string) {
  // Parlay cards: show ONLY the type. No legs/piernas count.
  if (kind === "BOOM_3") return "Boom";
  if ((kind || "").startsWith("SAFE")) return "Seguro";
  return "Parlay";
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

function ImgTeam({ src, alt }: { src?: string | null; alt: string }) {
  const [ok, setOk] = useState(true);

  if (!src || !ok) {
    const initials = initialsFromAlt(alt);
    return (
      <div
        aria-label={alt}
        title={alt}
        className="h-10 w-10 rounded-xl border border-white/10 bg-gradient-to-br from-white/20 via-white/10 to-white/5 flex items-center justify-center text-[11px] font-semibold tracking-wide text-white/75 select-none"
      >
        {initials}
      </div>
    );
  }

  // eslint-disable-next-line @next/next/no-img-element
  return (
    <img
      src={src}
      alt={alt}
      className="h-10 w-10 rounded-xl bg-white/5 border border-white/10 object-contain"
      onError={() => setOk(false)}
    />
  );
}


export default function Page() {
  const [contract, setContract] = useState<Contract | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<"classic" | "parley">("classic");
  const [stake, setStake] = useState<number>(50);

  useEffect(() => {
    const ctrl = new AbortController();
    getContract(ctrl.signal)
      .then(setContract)
      .catch((e: any) => setErr(e?.message || String(e)));
    return () => ctrl.abort();
  }, []);

  const classic = useMemo(() => {
    const raw = asPickList(contract);
    // Ya viene “10 picks” del backend. Aquí solo ordenamos un poco.
    return raw.slice().sort((a, b) => n(b.p_safe, -1e9) - n(a.p_safe, -1e9));
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
          <div className="card-inner p-6">
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
          <div className="card-inner p-6">
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
          className="card-inner p-6 md:p-8"
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
              <div className="flex items-center gap-2">
                <button className={tab === "classic" ? "badge badge-accent" : "badge"} onClick={() => setTab("classic")}>
                  Classic
                </button>
                <button className={tab === "parley" ? "badge badge-accent" : "badge"} onClick={() => setTab("parley")}>
                  Parley
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
              <div className="card-inner p-6 text-slate-300/80">Hoy no hay predicciones.</div>
            </section>
          ) : (
            <section className="grid gap-4 md:grid-cols-2">
              {classic.map((p, idx) => {
                const d = p.display || {};
                const home = d.home || {};
                const away = d.away || {};
                const profit = stake * (n(p.odds, NaN) - 1);

                return (
                  <article key={`${p.sport || "sport"}-${p.eventId || "event"}-${idx}`} className="card">
                    <div className="card-inner p-5">
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

                        <div className="flex flex-col items-end gap-1 shrink-0">
                          <div className="flex items-center gap-2">
                          <ImgTeam src={home?.logo} alt={home?.name || "Local"} />
                          <ImgTeam src={away?.logo} alt={away?.name || "Visitante"} />
                          </div>
                          {fmtLiveLine((d as any).live) ? (
                            <div className="subtle text-[11px] text-right">{fmtLiveLine((d as any).live)}</div>
                          ) : null}
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
                      </div>

                      {Number.isFinite(n(p.p_safe, NaN)) ? (
                        <div className="subtle text-xs mt-3">
                          Prob. estimada (segura): <span className="text-slate-100">{fmtPct(p.p_safe)}</span>
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

      {/* PARLEY */}
      {tab === "parley" && (
        <>
          {!parlays.length ? (
            <section className="card">
              <div className="card-inner p-6">
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

                return (
                  <article key={`${p.kind || "parley"}-${idx}`} className="card">
                    <div className="card-inner p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={p.kind === "BOOM_3" ? "badge badge-accent" : "badge"}>{tag}</span>
                                                      </div>

                          <div className="mt-2 text-lg font-semibold tracking-tight">{title}</div>

                          <div className="subtle text-xs mt-1">
                            Cuota combinada: <span className="text-slate-100">{fmtOdds(p.combined_odds)}</span> · Prob. est.:{" "}
                            <span className="text-slate-100">{fmtPct(p.prob_parlay)}</span>
                          </div>

                          <div className="subtle text-xs mt-1">
                            Ganancia potencial (con stake {fmtEur(stake)}): <span className="text-slate-100">{fmtEur(profit)}</span>
                          </div>

                          {p.note ? <div className="subtle text-xs mt-1">{p.note}</div> : null}
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3">
                        {legs.map((leg, i) => {
                          const dd = leg.display || {};
                          const h = dd.home || {};
                          const a = dd.away || {};
                          const hasTeams = Boolean(h.name || a.name);

                          return (
                            <div key={i} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                              <div className="mono">Selección {i + 1}</div>

                              <div className="mt-1 text-sm text-slate-100">
                                {hasTeams ? (
                                  <>
                                    {h.name || "Local"} vs {a.name || "Visitante"}
                                  </>
                                ) : (
                                  <>
                                    {sportEs(leg.sport)} · Evento {String(leg.eventId || "—")}
                                  </>
                                )}
                              </div>
                              {/* DF_LIVE_PARLAY_LEG */}
                              {hasTeams ? (
                                <div className="mt-2 grid grid-cols-3 items-center gap-2">
                                  <div className="flex justify-start">
                                    <ImgTeam src={h?.logo} alt={h?.name || "Local"} />
                                  </div>
                                  <div className="text-center">
                                    {fmtLiveLine((dd as any).live) ? (
                                      <div className="text-xs text-slate-100">{fmtLiveLine((dd as any).live)}</div>
                                    ) : (
                                      <div className="subtle text-xs">—</div>
                                    )}
                                  </div>
                                  <div className="flex justify-end">
                                    <ImgTeam src={a?.logo} alt={a?.name || "Visitante"} />
                                  </div>
                                </div>
                              ) : null}

                              <div className="subtle text-xs mt-1">
                                {sportEs((dd as any).sport || leg.sport)} · {(dd as any).league || "—"}
                              </div>

                              <div className="subtle text-xs mt-1">
                                {mercadoBonito(leg.market)} · <span className="text-slate-100">{selectionEs(leg.selection)}</span> · Cuota{" "}
                                <span className="text-slate-100">{fmtOdds(leg.odds)}</span>
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
    </main>
  );
}
