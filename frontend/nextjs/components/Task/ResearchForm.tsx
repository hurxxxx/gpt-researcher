import React, { useState, useEffect } from "react";
import ToneSelector from "../Settings/ToneSelector";
import { useAnalytics } from "../../hooks/useAnalytics";
import { ChatBoxSettings, Domain } from '@/types/data';

interface ResearchFormProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
  onFormSubmit?: (
    task: string,
    reportType: string,
    domains: Domain[]
  ) => void;
}

export default function ResearchForm({
  chatBoxSettings,
  setChatBoxSettings,
  onFormSubmit,
}: ResearchFormProps) {
  const { trackResearchQuery } = useAnalytics();
  const [task, setTask] = useState("");
  const [newDomain, setNewDomain] = useState('');

  // Destructure necessary fields from chatBoxSettings
  let { report_type, tone } = chatBoxSettings;

  const [domains, setDomains] = useState<Domain[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('domainFilters');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  
  useEffect(() => {
    localStorage.setItem('domainFilters', JSON.stringify(domains));
    setChatBoxSettings(prev => ({
      ...prev,
      domains: domains.map(domain => domain.value)
    }));
  }, [domains, setChatBoxSettings]);

  const handleAddDomain = (e: React.FormEvent) => {
    e.preventDefault();
    if (newDomain.trim()) {
      setDomains([...domains, { value: newDomain.trim() }]);
      setNewDomain('');
    }
  };

  const handleRemoveDomain = (domainToRemove: string) => {
    setDomains(domains.filter(domain => domain.value !== domainToRemove));
  };

  const onFormChange = (e: { target: { name: any; value: any } }) => {
    const { name, value } = e.target;
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      [name]: value,
    }));
  };

  const onToneChange = (e: { target: { value: any } }) => {
    const { value } = e.target;
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      tone: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onFormSubmit) {
      const updatedSettings = {
        ...chatBoxSettings,
        domains: domains.map(domain => domain.value)
      };
      setChatBoxSettings(updatedSettings);
      onFormSubmit(task, report_type, domains);
    }
  };

  return (
    <form
      method="POST"
      className="report_settings_static mt-3"
      onSubmit={handleSubmit}
    >
      <div className="form-group">
        <label htmlFor="report_type" className="agent_question">
          Report Type{" "}
        </label>
        <select
          name="report_type"
          value={report_type}
          onChange={onFormChange}
          className="form-control-static"
          required
        >
          <option value="research_report">
            Summary - Short and fast (~2 min)
          </option>
          {/*<option value="deep">Deep Research Report</option>*/}
          <option value="multi_agents">Multi Agents Report</option>
          <option value="detailed_report">
            Detailed - In depth and longer (~5 min)
          </option>
        </select>
      </div>

      <ToneSelector tone={tone} onToneChange={onToneChange} />

      <div className="mt-4 domain_filters">
        <div className="flex gap-2 mb-4">
          <label htmlFor="domain_filters" className="agent_question">
            Filter by domain{" "}
          </label>
          <input
            type="text"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            placeholder="Filter by domain (e.g., techcrunch.com)"
            className="input-static"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddDomain(e);
              }
            }}
          />
          <button
            type="button"
            onClick={handleAddDomain}
            className="button-static"
          >
            Add Domain
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {domains.map((domain, index) => (
            <div
              key={index}
              className="domain-tag-static"
            >
              <span className="domain-text-static">{domain.value}</span>
              <button
                type="button"
                onClick={() => handleRemoveDomain(domain.value)}
                className="domain-button-static"
              >
                X
              </button>
            </div>
          ))}
        </div>
      </div>
    </form>
  );
}
