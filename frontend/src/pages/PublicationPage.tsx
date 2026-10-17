import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import { apiRequest } from "../api";


type User = {
  id: number;
  name: string;
  email: string;
};

type Publication = {
  id: number;
  author_id: number;
  type: "startup" | "vacancy";
  title: string;
  description: string;
  looking_for: string;
  status: "active" | "closed";
  created_at: string;
  updated_at: string;
};

type Application = {
  id: number;
  publication_id: number;
  applicant_id: number;
  message: string;
  status:
    | "pending"
    | "accepted"
    | "rejected";
};


export function PublicationPage() {
  const { id } = useParams();

  const navigate = useNavigate();

  const [publication, setPublication] =
    useState<Publication | null>(null);

  const [user, setUser] =
    useState<User | null>(null);

  const [application, setApplication] =
    useState<Application | null>(null);

  const [message, setMessage] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [sending, setSending] =
    useState(false);

  const [error, setError] =
    useState("");


  useEffect(() => {
    async function loadPage() {
      try {
        const [
          publicationData,
          userData,
          sentApplications,
        ] = await Promise.all([
          apiRequest(
            `/publications/${id}`,
          ),

          apiRequest("/users/me"),

          apiRequest(
            "/applications/sent",
          ),
        ]);

        setPublication(
          publicationData,
        );

        setUser(userData);

        const existing =
          sentApplications.find(
            (
              item: Application,
            ) =>
              item.publication_id ===
              Number(id),
          );

        if (existing) {
          setApplication(existing);
        }
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Не удалось загрузить публикацию",
        );
      } finally {
        setLoading(false);
      }
    }

    loadPage();
  }, [id]);


  async function handleApply(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setSending(true);
    setError("");

    try {
      const data =
        await apiRequest(
          `/publications/${id}/applications`,
          {
            method: "POST",
            body: JSON.stringify({
              message,
            }),
          },
        );

      setApplication(data);
      setMessage("");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Не удалось отправить отклик",
      );
    } finally {
      setSending(false);
    }
  }


  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-8 text-slate-500">
        Загружаем публикацию...
      </div>
    );
  }


  if (error && !publication) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-3xl">
          <Link
            to="/"
            className="text-sm font-semibold text-indigo-600"
          >
            ← Вернуться в ленту
          </Link>

          <div className="mt-6 rounded-2xl bg-red-50 p-5 text-red-700">
            {error}
          </div>
        </div>
      </div>
    );
  }


  if (!publication) {
    return null;
  }


  const isOwner =
    user?.id === publication.author_id;


  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4 sm:px-6">
          <button
            onClick={() =>
              navigate("/")
            }
            className="text-sm font-semibold text-slate-600 hover:text-slate-900"
          >
            ← Лента
          </button>

          <div className="font-bold text-slate-900">
            Business Club
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-12">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span
              className={
                publication.type ===
                "startup"
                  ? "rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700"
                  : "rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700"
              }
            >
              {publication.type ===
              "startup"
                ? "🚀 Стартап"
                : "💼 Вакансия"}
            </span>

            <span className="text-sm text-slate-400">
              {new Intl.DateTimeFormat(
                "ru-RU",
                {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                },
              ).format(
                new Date(
                  publication.created_at,
                ),
              )}
            </span>
          </div>

          <h1 className="mt-6 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            {publication.title}
          </h1>

          <div className="mt-3 text-sm text-slate-500">
            {isOwner
              ? "Ваша публикация"
              : `Автор: участник #${publication.author_id}`}
          </div>

          <div className="mt-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              О проекте
            </h2>

            <p className="mt-3 whitespace-pre-line text-base leading-7 text-slate-700">
              {publication.description}
            </p>
          </div>

          <div className="mt-8 rounded-2xl bg-slate-50 p-5">
            <div className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              Кого ищут
            </div>

            <div className="mt-2 font-medium text-slate-800">
              {publication.looking_for}
            </div>
          </div>
        </article>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {isOwner && (
          <div className="mt-6 rounded-3xl border border-indigo-100 bg-indigo-50 p-6">
            <div className="font-semibold text-indigo-900">
              Это ваша публикация
            </div>

            <p className="mt-1 text-sm text-indigo-700">
              Вы не можете откликнуться
              на собственное предложение.
            </p>
          </div>
        )}

        {!isOwner &&
          publication.status ===
            "active" &&
          !application && (
            <form
              onSubmit={handleApply}
              className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
            >
              <h2 className="text-2xl font-bold text-slate-900">
                Откликнуться
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Расскажите автору, почему
                вам интересен проект и чем
                вы можете быть полезны.
              </p>

              <textarea
                value={message}
                onChange={(event) =>
                  setMessage(
                    event.target.value,
                  )
                }
                minLength={3}
                maxLength={2000}
                rows={6}
                placeholder="Например: есть опыт FastAPI и PostgreSQL, хотелось бы помочь с backend..."
                className="mt-5 w-full resize-none rounded-2xl border border-slate-300 px-4 py-3 outline-none focus:border-indigo-500"
                required
              />

              <button
                type="submit"
                disabled={sending}
                className="mt-4 w-full rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 sm:w-auto"
              >
                {sending
                  ? "Отправляем..."
                  : "Отправить отклик"}
              </button>
            </form>
          )}

        {application && (
          <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              Ваш отклик
            </div>

            <div className="mt-3">
              <ApplicationStatusBadge
                status={
                  application.status
                }
              />
            </div>

            <p className="mt-4 whitespace-pre-line text-slate-600">
              {application.message}
            </p>
          </div>
        )}

        {!isOwner &&
          publication.status ===
            "closed" && (
            <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 text-slate-600">
              Эта публикация закрыта.
              Отправить новый отклик уже
              нельзя.
            </div>
          )}
      </section>
    </main>
  );
}


function ApplicationStatusBadge({
  status,
}: {
  status:
    | "pending"
    | "accepted"
    | "rejected";
}) {
  if (status === "accepted") {
    return (
      <span className="inline-flex rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">
        ✓ Принят
      </span>
    );
  }

  if (status === "rejected") {
    return (
      <span className="inline-flex rounded-full bg-red-50 px-3 py-1 text-sm font-semibold text-red-700">
        Отклонён
      </span>
    );
  }

  return (
    <span className="inline-flex rounded-full bg-amber-50 px-3 py-1 text-sm font-semibold text-amber-700">
      На рассмотрении
    </span>
  );
}