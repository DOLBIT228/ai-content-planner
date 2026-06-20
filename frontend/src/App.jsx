import { useEffect, useMemo, useState } from 'react';

const CHANNEL_FORMATS = {
  Instagram: ['Reels', 'Stories', 'Posts', 'Carousels'],
  TikTok: ['Videos', 'Stories'],
  Facebook: ['Posts', 'Stories', 'Videos'],
  LinkedIn: ['Posts', 'Carousels'],
};

const initialCampaign = {
  title: '',
  start_date: '',
  end_date: '',
  brief: '',
  channel_name: 'Instagram',
  post_count: 0,
  carousel_count: 0,
  reel_count: 0,
  stories_count: 0,
  image_percentage: 70,
};

async function api(path, options = {}) {
  const headers = options.rawBody ? options.headers || {} : { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const { rawBody, ...fetchOptions } = options;
  const response = await fetch(path, { headers, ...fetchOptions });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

const toNumber = (value) => Number(value || 0);
const formatLabels = { post_count: 'Posts', carousel_count: 'Carousels', reel_count: 'Reels', stories_count: 'Stories' };

export default function App() {
  const [form, setForm] = useState(initialCampaign);
  const [campaigns, setCampaigns] = useState([]);
  const [activeCampaignId, setActiveCampaignId] = useState('');
  const [campaignDetails, setCampaignDetails] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [notice, setNotice] = useState('Додайте базу знань, заповніть параметри та створіть кампанію.');
  const [isGenerating, setIsGenerating] = useState(false);

  const salesPercentage = 100 - toNumber(form.image_percentage);
  const selectedFormats = useMemo(() => CHANNEL_FORMATS[form.channel_name] || CHANNEL_FORMATS.Instagram, [form.channel_name]);

  const run = async (task) => {
    try { await task(); } catch (error) { setNotice(`Помилка: ${error.message}`); }
  };

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const refreshCampaigns = async (selectedId = activeCampaignId) => {
    const data = await api('/campaigns');
    setCampaigns(data);
    if (selectedId) setActiveCampaignId(String(selectedId));
    if (!selectedId && data[0]) setActiveCampaignId(String(data[0].id));
  };

  const refreshDocuments = async () => setDocuments(await api('/knowledge-documents'));

  const loadCampaign = async (id = activeCampaignId) => {
    if (!id) return;
    setCampaignDetails(await api(`/campaigns/${id}`));
  };

  const uploadDocument = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const body = await file.arrayBuffer();
    await api(`/knowledge-documents?filename=${encodeURIComponent(file.name)}`, { method: 'POST', body, rawBody: true, headers: { 'Content-Type': file.type || 'application/octet-stream' } });
    setNotice(`Файл "${file.name}" додано до бази знань.`);
    await refreshDocuments();
    event.target.value = '';
  };

  const createAndGenerateCampaign = async () => {
    setIsGenerating(true);
    try {
      const payload = {
        title: form.title,
        start_date: form.start_date,
        end_date: form.end_date,
        brief: form.brief,
        sales_percentage: salesPercentage,
        image_percentage: toNumber(form.image_percentage),
        channels: [{
          channel_name: form.channel_name,
          post_count: toNumber(form.post_count),
          carousel_count: toNumber(form.carousel_count),
          reel_count: toNumber(form.reel_count),
          stories_count: toNumber(form.stories_count),
        }],
      };
      const campaign = await api('/campaigns', { method: 'POST', body: JSON.stringify(payload) });
      setActiveCampaignId(String(campaign.id));
      await api(`/campaigns/${campaign.id}/generate-plan`, { method: 'POST' });
      await refreshCampaigns(campaign.id);
      await loadCampaign(campaign.id);
      setNotice('AI згенерував контент-план. Перегляньте одиниці контенту нижче.');
    } finally { setIsGenerating(false); }
  };

  const entries = campaignDetails?.entries || [];

  useEffect(() => { run(async () => { await refreshCampaigns(); await refreshDocuments(); }); }, []);

  return (
    <main className="app-shell">
      <header className="hero">
        <p className="eyebrow">AI Content Planner</p>
        <h1>Мінімалістичний генератор кампаній для маркетолога</h1>
        <p>Створіть кампанію, підключіть файли з бази знань і отримайте розклад контенту по днях через OpenRouter модель <strong>openai/gpt-4.1-mini</strong>.</p>
      </header>

      <section className="panel grid-two">
        <div>
          <p className="eyebrow">Сторінка 1</p>
          <h2>Нова кампанія</h2>
          <label>Назва кампанії<input placeholder="Наприклад: Launch FW 2026" value={form.title} onChange={(event) => updateField('title', event.target.value)} /></label>
          <label>Короткий опис / промт для моделі<textarea rows="5" placeholder="Опишіть продукт, ЦА, tone of voice, обмеження та ціль кампанії" value={form.brief} onChange={(event) => updateField('brief', event.target.value)} /></label>
          <div className="row"><label>Період від<input type="date" value={form.start_date} onChange={(event) => updateField('start_date', event.target.value)} /></label><label>Період до<input type="date" value={form.end_date} onChange={(event) => updateField('end_date', event.target.value)} /></label></div>
          <label>Канал<select value={form.channel_name} onChange={(event) => updateField('channel_name', event.target.value)}>{Object.keys(CHANNEL_FORMATS).map((channel) => <option key={channel}>{channel}</option>)}</select></label>
          <div className="format-help"><strong>Доступні формати:</strong> {selectedFormats.join(', ')}</div>
          <div className="format-grid">{Object.entries(formatLabels).map(([field, label]) => <label key={field}>{label}<input type="number" min="0" value={form[field]} onChange={(event) => updateField(field, event.target.value)} /></label>)}</div>
          <label>Баланс контенту: {form.image_percentage}% імідж / {salesPercentage}% продаж<input type="range" min="0" max="100" value={form.image_percentage} onChange={(event) => updateField('image_percentage', event.target.value)} /></label>
          <button className="primary" disabled={isGenerating} onClick={() => run(createAndGenerateCampaign)}>{isGenerating ? 'Генеруємо через AI…' : 'Створити кампанію'}</button>
        </div>
        <aside className="knowledge-card">
          <p className="eyebrow">База знань</p>
          <h2>Файли для контексту</h2>
          <p>Завантажені матеріали автоматично додаються до промту генерації кампанії.</p>
          <input type="file" onChange={(event) => run(() => uploadDocument(event))} accept=".txt,.md,.csv,.json,.html,.xml,.pdf,.doc,.docx" />
          <div className="doc-list">{documents.length ? documents.map((document) => <div key={document.id}>#{document.id} {document.filename}</div>) : <span>Файлів ще немає.</span>}</div>
        </aside>
      </section>

      <section className="panel">
        <div className="section-head"><div><p className="eyebrow">Review</p><h2>Згенерований контент-план</h2></div><label>Кампанія<select value={activeCampaignId} onChange={(event) => setActiveCampaignId(event.target.value)}><option value="">Оберіть кампанію</option>{campaigns.map((campaign) => <option key={campaign.id} value={campaign.id}>#{campaign.id} — {campaign.title} ({campaign.status})</option>)}</select></label><button onClick={() => run(() => loadCampaign())}>Відкрити</button></div>
        <p className="notice">{notice}</p>
        {!entries.length && <p className="empty">Після генерації тут зʼявиться календар із темою, ціллю, описом і готовим контентом.</p>}
        <div className="cards">{entries.map((entry) => <article className="content-card" key={entry.id}><div className="card-meta"><span>{entry.publish_date}</span><span>{entry.format}</span><span>{entry.goal}</span></div><h3>{entry.topic}</h3><p>{entry.short_description}</p><p className="angle">{entry.angle}</p><pre>{entry.post_text}</pre></article>)}</div>
      </section>
    </main>
  );
}
