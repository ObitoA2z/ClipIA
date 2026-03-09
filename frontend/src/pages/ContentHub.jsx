import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import toast from "react-hot-toast";

import api from "../services/api";
import Card from "../components/ui/Card";

const TABS = [
  { key: "blog", label: "Blog" },
  { key: "twitter_thread", label: "Twitter" },
  { key: "linkedin_post", label: "LinkedIn" },
  { key: "show_notes", label: "Show Notes" },
  { key: "quote_cards", label: "Quote Cards" },
];

async function fetchContentHub(videoId) {
  const { data } = await api.get(`/content-repurpose/${videoId}`);
  return data;
}

function ContentHub() {
  const { videoId } = useParams();
  const [activeTab, setActiveTab] = useState("blog");

  const contentQuery = useQuery({
    queryKey: ["content-hub", videoId],
    queryFn: () => fetchContentHub(videoId),
    enabled: Boolean(videoId),
  });

  const content = contentQuery.data?.content || {};

  const tabContent = useMemo(() => {
    if (activeTab === "twitter_thread") {
      return Array.isArray(content.twitter_thread) ? content.twitter_thread.join("\n\n") : "";
    }
    if (activeTab === "quote_cards") {
      return "";
    }
    return String(content[activeTab] || "");
  }, [activeTab, content]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(tabContent);
      toast.success("Contenu copie");
    } catch {
      toast.error("Impossible de copier");
    }
  };

  return (
    <section className="page">
      <Card>
        <p className="caption">CONTENT HUB</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Repurposing multi-format
        </h2>
        <p className="muted">Video: {contentQuery.data?.video?.title || videoId}</p>
      </Card>

      <Card>
        <div className="inline-actions">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              className={`ui-btn ${activeTab === tab.key ? "ui-btn-primary" : "ui-btn-secondary"}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {contentQuery.isLoading ? <div className="skeleton" style={{ marginTop: 12 }} /> : null}

        {!contentQuery.isLoading && activeTab !== "quote_cards" ? (
          <>
            <pre className="content-preview">{tabContent}</pre>
            <button type="button" className="ui-btn ui-btn-secondary" onClick={handleCopy}>
              Copier
            </button>
          </>
        ) : null}

        {!contentQuery.isLoading && activeTab === "quote_cards" ? (
          <div className="grid grid-3" style={{ marginTop: 14 }}>
            {(content.quote_cards || []).map((item) => (
              <div key={item.url} className="ui-card" style={{ padding: 12 }}>
                <img src={item.url} alt="Quote card" loading="lazy" style={{ borderRadius: 10 }} />
                <a href={item.url} target="_blank" rel="noreferrer" className="muted" style={{ fontSize: 12 }}>
                  Ouvrir
                </a>
              </div>
            ))}
            {!content.quote_cards?.length ? <p className="muted">Aucune quote card disponible.</p> : null}
          </div>
        ) : null}
      </Card>
    </section>
  );
}

export default ContentHub;
