"use client";

import { useEffect, useState } from "react";

type Selection = {
  name: string;
  odds: number;
  probability: number;
};

type RiskLevel = "green" | "yellow" | "red";

type Bet = {
  id: string;
  type: "classic" | "parlay";
  title: string;
  sport: string;
  event: string;
  market: string;
  startTime: string;
  status: string;
  selections: Selection[];

  totalProbability: number;
  totalOdds: number;
  stake: number;
  potentialWin: number;
  riskLevel: RiskLevel;
  isPremium: boolean;
};

type ApiResponse = {
  premiumTop3: Bet[];
  classic: Bet[];
  parlay: Bet[];
};

const riskColors: Record<RiskLevel, string> = {
  green: "bg-green-500",
  yellow: "bg-yellow-500",
  red: "bg-red-500",
};

export default function Home() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"classic" | "parlay">("classic");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/bets/today")
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const bets = activeTab === "classic" ? data?.classic : data?.parlay;

  return (
    <main className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold">Bot Ultimate Prediction</h1>

      {/* ⭐ TOP 3 PREMIUM */}
      {!loading && data?.premiumTop3 && data.premiumTop3.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-yellow-400">
            ⭐ Top 3 Premium del día
          </h2>

          <ul className="space-y-4">
            {data.premiumTop3.map((bet) => (
              <li
                key={bet.id}
                className="bg-[#0B1220] border border-yellow-500/40 rounded-xl p-5 space-y-4"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm text-yellow-400">{bet.sport}</div>
                    <div className="font-semibold text-lg">{bet.title}</div>
                    <div className="text-sm text-gray-400">{bet.event}</div>
                  </div>

                  <span className="text-xs bg-yellow-500 text-black px-2 py-1 rounded-full font-semibold">
                    ⭐ PREMIUM
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm pt-2 border-t border-[#1F2933]">
                  <div>
                    <div className="text-gray-400">Probabilidad</div>
                    <div className="font-semibold">
                      {Math.round(bet.totalProbability * 100)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-400">Cuota</div>
                    <div className="font-semibold">{bet.totalOdds}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Stake</div>
                    <div className="font-semibold">{bet.stake} €</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Ganancia</div>
                    <div className="font-semibold text-green-400">
                      {bet.potentialWin} €
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab("classic")}
          className={`px-4 py-2 rounded-lg text-sm ${
            activeTab === "classic"
              ? "bg-blue-600 text-white"
              : "bg-[#111827] text-gray-400"
          }`}
        >
          Clásicas
        </button>

        <button
          onClick={() => setActiveTab("parlay")}
          className={`px-4 py-2 rounded-lg text-sm ${
            activeTab === "parlay"
              ? "bg-purple-600 text-white"
              : "bg-[#111827] text-gray-400"
          }`}
        >
          Multi‑Deporte (Parley)
        </button>
      </div>

      {loading && <div className="text-gray-400">Cargando apuestas…</div>}

      {!loading && bets && (
        <ul className="space-y-6">
          {bets.map((bet) => (
            <li
              key={bet.id}
              className="bg-[#0F172A] rounded-xl p-5 space-y-4"
            >
              {/* Header */}
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-sm text-blue-400">{bet.sport}</div>
                  <div className="font-semibold text-lg">{bet.title}</div>
                  <div className="text-sm text-gray-400">{bet.event}</div>
                </div>

                <div className="flex gap-2 items-center">
                  {bet.isPremium && (
                    <span className="text-xs bg-yellow-500 text-black px-2 py-1 rounded-full font-semibold">
                      ⭐ PREMIUM
                    </span>
                  )}
                  <span
                    className={`text-xs text-white px-2 py-1 rounded-full ${riskColors[bet.riskLevel]}`}
                  >
                    {bet.riskLevel.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="text-sm text-gray-300">
                Mercado: <span className="text-gray-400">{bet.market}</span>
              </div>

              {/* Selections */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {bet.selections.map((sel, idx) => (
                  <div
                    key={idx}
                    className="border border-[#1F2933] rounded-lg p-3"
                  >
                    <div className="font-medium">{sel.name}</div>
                    <div className="text-sm text-gray-400">
                      Probabilidad: {Math.round(sel.probability * 100)}% · Cuota{" "}
                      {sel.odds}
                    </div>
                  </div>
                ))}
              </div>

              {/* Totales */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-[#1F2933] text-sm">
                <div>
                  <div className="text-gray-400">Probabilidad total</div>
                  <div className="font-semibold">
                    {Math.round(bet.totalProbability * 100)}%
                  </div>
                </div>

                <div>
                  <div className="text-gray-400">Cuota total</div>
                  <div className="font-semibold">{bet.totalOdds}</div>
                </div>

                <div>
                  <div className="text-gray-400">Stake</div>
                  <div className="font-semibold">{bet.stake} €</div>
                </div>

                <div>
                  <div className="text-gray-400">Ganancia potencial</div>
                  <div className="font-semibold text-green-400">
                    {bet.potentialWin} €
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
