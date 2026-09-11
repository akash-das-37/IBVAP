import React from 'react';
import MetricsGrid from '../components/MetricsGrid';
import LiveFeed from '../components/LiveFeed';
import ActiveAlertsCard from '../components/ActiveAlertsCard';
import RecentEventsTimeline from '../components/RecentEventsTimeline';

export default function DashboardPage({
  liveStats,
  historicalStats,
  currentCamera,
  alerts,
  events,
  zones = [],
  onAlertUpdated,
  onSourceChanged
}) {
  return (
    <div className="flex-1 overflow-y-auto p-4 flex flex-col space-y-4">
      {/* 1. Real-time Telemetry Metrics Grid */}
      <MetricsGrid liveStats={liveStats} historicalStats={historicalStats} />

      {/* 2. Main Live Feed and Active Alerts Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-[440px]">
        <div className="lg:col-span-2 h-full min-h-[420px]">
          <LiveFeed
            liveStats={liveStats}
            currentCamera={currentCamera}
            zones={zones}
            onSourceChanged={onSourceChanged}
          />
        </div>
        <div className="h-full min-h-[420px]">
          <ActiveAlertsCard
            alerts={alerts}
            onAlertUpdated={onAlertUpdated}
          />
        </div>
      </div>

      {/* 3. Bottom Timeline View */}
      <div className="h-56">
        <RecentEventsTimeline events={events} />
      </div>
    </div>
  );
}
