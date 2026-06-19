import { useEffect, useState } from 'react';

const initialCampaign = {
  title: 'Luxury Skincare Launch',
  start_date: '2026-07-01',
  end_date: '2026-07-07',
  brief: 'Premium skincare for busy founders. Elegant, concise, confident.',
  sales_percentage: 50,
  image_percentage: 25,
  channel_name: 'Instagram',
  post_count: 1,
  carousel_count: 1,
  reel_count: 1,
  stories_count: 1,
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(data));
  return data;
}

function toNumber(value) {
  return Number(value || 0);
}

export default function App() {
  const [form, setForm] = useState(initialCampaign);
  const [campaigns, setCampaigns] = useState([]);
  const [activeCampaignId, setActiveCampaignId] = useState('');
  const [campaignDetails, setCampaignDetails] = useState(null);
  const [output, setOutput] = useState('Ready.');
  const [feedbackByEntry, setFeedbackByEntry] = useState({});

  const show = (data) => setOutput(typeof data === 'string' ? data : JSON.stringify(data, null, 2));

  const refreshCampaigns = async (selectedId = activeCampaignId) => {
    const data = await api('/campaigns');
    setCampaigns(data);
    if (selectedId) setActiveCampaignId(String(selectedId));
    if (!selectedId && data[0]) setActiveCampaignId(String(data[0].id));
    show(data);
  };

  const loadCampaign = async (id = activeCampaignId) => {
    if (!id) return;
    const data = await api(`/campaigns/${id}`);
    setCampaignDetails(data);
    setFeedbackByEntry(Object.fromEntries((data.entries || []).map((entry) => [entry.id, 'make it more premium, less text'])));
    show(data);
  };

  const run = async (task) => {
    try {
      await task();
    } catch (error) {
      show(`Error: ${error.message}`);
    }
  };

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const createCampaign = async () => {
    const payload = {
      title: form.title,
      start_date: form.start_date,
      end_date: form.end_date,
      brief: form.brief,
      sales_percentage: toNumber(form.sales_percentage),
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
    show(campaign);
    await refreshCampaigns(campaign.id);
    await loadCampaign(campaign.id);
  };

  const generatePlan = async () => {
    if (!activeCampaignId) return show('Create or select a campaign first.');
    const entries = await api(`/campaigns/${activeCampaignId}/generate-plan`, { method: 'POST' });
    show(entries);
    await loadCampaign(activeCampaignId);
    await refreshCampaigns(activeCampaignId);
  };

  const entryAction = async (entryId, action) => {
    let result;
    if (action === 'generate') result = await api(`/content-entries/${entryId}/generate`, { method: 'POST' });
    if (action === 'approve') result = await api(`/content-entries/${entryId}/approve`, { method: 'POST' });
    if (action === 'reject') result = await api(`/content-entries/${entryId}/reject`, { method: 'POST' });
    if (action === 'delete') result = await api(`/content-entries/${entryId}`, { method: 'DELETE' });
    if (action === 'regenerate') {
      result = await api(`/content-entries/${entryId}/regenerate`, {
        method: 'POST',
        body: JSON.stringify({ feedback: feedbackByEntry[entryId] || '' }),
      });
    }
    show(result || `${action} completed`);
    await loadCampaign(activeCampaignId);
  };

  useEffect(() => {
    run(() => refreshCampaigns());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const entries = campaignDetails?.entries || [];

  return (
    <main>
      <h1>AI Content OS — Basic React UI</h1>
      <p className="muted">Мінімальний React інтерфейс для перевірки workflow: Campaign → Plan → Generate → Review.</p>

      <section>
        <h2>1. Create Campaign</h2>
        <label>Title <input value={form.title} onChange={(event) => updateField('title', event.target.value)} /></label>
        <div className="row">
          <label>Start date <input type="date" value={form.start_date} onChange={(event) => updateField('start_date', event.target.value)} /></label>
          <label>End date <input type="date" value={form.end_date} onChange={(event) => updateField('end_date', event.target.value)} /></label>
        </div>
        <label>Brief <textarea rows="4" value={form.brief} onChange={(event) => updateField('brief', event.target.value)} /></label>
        <div className="row">
          <label>Sales % <input type="number" min="0" max="100" value={form.sales_percentage} onChange={(event) => updateField('sales_percentage', event.target.value)} /></label>
          <label>Image % <input type="number" min="0" max="100" value={form.image_percentage} onChange={(event) => updateField('image_percentage', event.target.value)} /></label>
        </div>
        <h3>Channel volume</h3>
        <label>Channel name <input value={form.channel_name} onChange={(event) => updateField('channel_name', event.target.value)} /></label>
        <div className="row">
          <label>Posts <input type="number" min="0" value={form.post_count} onChange={(event) => updateField('post_count', event.target.value)} /></label>
          <label>Carousels <input type="number" min="0" value={form.carousel_count} onChange={(event) => updateField('carousel_count', event.target.value)} /></label>
          <label>Reels <input type="number" min="0" value={form.reel_count} onChange={(event) => updateField('reel_count', event.target.value)} /></label>
          <label>Stories <input type="number" min="0" value={form.stories_count} onChange={(event) => updateField('stories_count', event.target.value)} /></label>
        </div>
        <button onClick={() => run(createCampaign)}>Create campaign</button>
        <button onClick={() => run(() => refreshCampaigns())}>Refresh campaigns</button>
      </section>

      <section>
        <h2>2. Campaigns</h2>
        <label>Active campaign
          <select value={activeCampaignId} onChange={(event) => setActiveCampaignId(event.target.value)}>
            <option value="">No campaign selected</option>
            {campaigns.map((campaign) => (
              <option key={campaign.id} value={campaign.id}>#{campaign.id} — {campaign.title} ({campaign.status})</option>
            ))}
          </select>
        </label>
        <button onClick={() => run(() => loadCampaign())}>Load selected campaign</button>
        <button onClick={() => run(generatePlan)}>Generate plan</button>
        {campaignDetails && <pre>{JSON.stringify(campaignDetails.campaign, null, 2)}</pre>}
      </section>

      <section>
        <h2>3. Content Entries</h2>
        <p className="muted">Generate пише текст тільки для конкретного entry. Planning не генерує post_text.</p>
        {!entries.length && <p>No entries yet. Generate a plan first.</p>}
        {!!entries.length && (
          <table>
            <thead>
              <tr><th>ID</th><th>Date</th><th>Format</th><th>Goal</th><th>Plan</th><th>Status</th><th>Post text</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td>#{entry.id}</td>
                  <td>{entry.publish_date}</td>
                  <td>{entry.format}</td>
                  <td>{entry.goal}</td>
                  <td><strong>{entry.topic}</strong><br />{entry.short_description}<br /><em>{entry.angle}</em></td>
                  <td>{entry.status}</td>
                  <td><pre>{entry.post_text || 'No generated text yet.'}</pre></td>
                  <td>
                    <button onClick={() => run(() => entryAction(entry.id, 'generate'))}>Generate</button>
                    <button onClick={() => run(() => entryAction(entry.id, 'approve'))}>Approve</button>
                    <button onClick={() => run(() => entryAction(entry.id, 'reject'))}>Reject</button>
                    <button onClick={() => run(() => entryAction(entry.id, 'delete'))}>Delete</button>
                    <label>Feedback
                      <textarea
                        rows="2"
                        value={feedbackByEntry[entry.id] || ''}
                        onChange={(event) => setFeedbackByEntry((current) => ({ ...current, [entry.id]: event.target.value }))}
                      />
                    </label>
                    <button onClick={() => run(() => entryAction(entry.id, 'regenerate'))}>Regenerate</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>Raw API response</h2>
        <pre>{output}</pre>
      </section>
    </main>
  );
}
