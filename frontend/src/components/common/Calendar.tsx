/**
 * Calendar — V3 month grid with optional scheduled-date markers.
 * Used in PublishAdvisorPage for publish-calendar view.
 */
import React from 'react';

interface CalendarProps {
  year: number;
  month: number; // 0-indexed
  today: number; // day-of-month highlighted
  scheduled: number[]; // days of the month marked
  onDayClick?: (day: number) => void;
}

const WEEK_LABELS = ['一', '二', '三', '四', '五', '六', '日'];

const Calendar = ({
  year,
  month,
  today,
  scheduled,
  onDayClick,
}: CalendarProps): React.ReactElement => {
  const firstWeekday = new Date(year, month, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  // Convert Sun=0 to Mon=0
  const offset = (firstWeekday + 6) % 7;
  const scheduledSet = new Set(scheduled);
  const cells: Array<{ day: number | null; isToday: boolean; isScheduled: boolean }> = [];
  for (let i = 0; i < offset; i += 1) {
    cells.push({ day: null, isToday: false, isScheduled: false });
  }
  for (let d = 1; d <= daysInMonth; d += 1) {
    cells.push({ day: d, isToday: d === today, isScheduled: scheduledSet.has(d) });
  }
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(7, 1fr)',
        gap: 2,
        textAlign: 'center',
      }}
    >
      {WEEK_LABELS.map((d) => (
        <div
          key={d}
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--v3-text-sec)',
            padding: '6px 0',
          }}
        >
          {d}
        </div>
      ))}
      {cells.map((c, i) => {
        if (c.day === null) {
          return <div key={i} style={{ padding: '7px 0' }} aria-hidden="true" />;
        }
        return (
          <button
            key={i}
            type="button"
            disabled={!onDayClick}
            onClick={() => onDayClick?.(c.day as number)}
            aria-current={c.isToday ? 'date' : undefined}
            style={{
              padding: '7px 0',
              borderRadius: 4,
              fontSize: 12,
              color: 'var(--v3-text)',
              fontWeight: c.isToday ? 600 : 400,
              background: c.isToday ? 'var(--v3-accent-soft)' : 'transparent',
              border: 'none',
              cursor: onDayClick ? 'pointer' : 'default',
              fontFamily: 'inherit',
              position: 'relative',
            }}
          >
            {c.day}
            {c.isScheduled && (
              <span
                aria-hidden="true"
                style={{
                  position: 'absolute',
                  bottom: 2,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: 4,
                  height: 4,
                  borderRadius: '50%',
                  background: 'var(--v3-text)',
                }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
};

export default Calendar;
