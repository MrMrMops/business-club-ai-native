import { useEffect, useState } from "react";
import { apiRequest } from "../api";

type Readiness = {
  accepted_count: number;
  required_skills: string[];
  covered_skills: string[];
  missing_skills: string[];
  recommendation: string;
  limitation: string;
};

export function TeamReadiness({ publicationId, requirements }: {
  publicationId: number;
  requirements: string;
}) {
  const [data, setData] = useState<Readiness | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    apiRequest(`/publications/${publicationId}/team-readiness`)
      .then((result: Readiness) => { if (!cancelled) setData(result); })
      .catch(() => { if (!cancelled) setError(true); });
    return () => { cancelled = true; };
  }, [publicationId, requirements, attempt]);

  return (
    <section className="mt-5 rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4 sm:p-5">
      <h3 className="font-bold text-slate-900">Компетенции команды</h3>
      {error ? (
        <div className="mt-3 text-sm text-slate-600" role="status">
          Не удалось загрузить анализ команды.
          <button type="button" className="ml-2 font-semibold text-indigo-700" onClick={() => {
            setError(false); setData(null); setAttempt(attempt + 1);
          }}>Повторить</button>
        </div>
      ) : !data ? (
        <p className="mt-3 text-sm text-slate-500" role="status">Анализируем указанные навыки…</p>
      ) : (
        <>
          <p className="mt-2 text-sm text-slate-600">
            {data.accepted_count === 0
              ? "Принятых откликов пока нет. Рассмотрите кандидатов во «Входящих», чтобы начать формировать команду."
              : `Принятых участников: ${data.accepted_count}`}
          </p>
          {data.required_skills.length > 0 && (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {[
                { title: "Покрытые навыки", skills: data.covered_skills, color: "bg-emerald-50 text-emerald-800", empty: "Совпадений пока нет" },
                { title: "Пока не покрыты", skills: data.missing_skills, color: "bg-amber-50 text-amber-900", empty: "Все распознанные навыки покрыты" },
              ].map((group) => (
                <div key={group.title} className="min-w-0">
                  <h4 className="text-sm font-semibold text-slate-800">{group.title}</h4>
                  {group.skills.length ? (
                    <ul className="mt-2 flex flex-wrap gap-2" aria-label={group.title}>
                      {group.skills.map((skill) => (
                        <li key={skill} className={`rounded-full px-3 py-1 text-xs font-medium ${group.color}`}>{skill}</li>
                      ))}
                    </ul>
                  ) : <p className="mt-2 text-sm text-slate-500">{group.empty}</p>}
                </div>
              ))}
            </div>
          )}
          <p className="mt-4 break-words text-sm leading-6 text-slate-700">{data.recommendation}</p>
          <p className="mt-3 text-xs leading-5 text-slate-500">{data.limitation}</p>
        </>
      )}
    </section>
  );
}
