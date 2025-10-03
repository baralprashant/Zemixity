/**
 * Analytics/Telemetry Module
 *
 * Simple analytics tracking for usage patterns.
 * Can be extended to integrate with Google Analytics, Plausible, etc.
 */

type AnalyticsEvent = {
  event: string;
  properties?: Record<string, unknown>;
  timestamp: string;
};

class Analytics {
  private enabled: boolean;
  private events: AnalyticsEvent[] = [];

  constructor() {
    // Enable analytics only in production
    this.enabled = process.env.NODE_ENV === 'production';
  }

  /**
   * Track a custom event
   */
  track(event: string, properties?: Record<string, unknown>) {
    if (!this.enabled) {
      console.log('[Analytics - Dev]', event, properties);
      return;
    }

    const analyticsEvent: AnalyticsEvent = {
      event,
      properties,
      timestamp: new Date().toISOString(),
    };

    this.events.push(analyticsEvent);

    // Send to your analytics service here
    // Example: Google Analytics, Plausible, Mixpanel, etc.
    this.sendEvent(analyticsEvent);
  }

  /**
   * Track page views
   */
  pageView(path: string) {
    this.track('page_view', { path });
  }

  /**
   * Track search queries
   */
  search(query: string) {
    this.track('search', {
      query_length: query.length,
      // Don't send the actual query for privacy
    });
  }

  /**
   * Track follow-up questions
   */
  followUp(threadId: string) {
    this.track('follow_up', { thread_id: threadId });
  }

  /**
   * Track thread actions
   */
  threadAction(action: 'create' | 'delete' | 'rename' | 'pin' | 'export' | 'share') {
    this.track('thread_action', { action });
  }

  /**
   * Track related question clicks
   */
  relatedQuestionClick(question: string) {
    this.track('related_question_click', {
      question_length: question.length,
    });
  }

  /**
   * Track source clicks
   */
  sourceClick(domain: string) {
    this.track('source_click', { domain });
  }

  /**
   * Send event to analytics service
   */
  private sendEvent(_event: AnalyticsEvent) {
    // Example: Send to your backend analytics endpoint
    if (typeof window !== 'undefined') {
      // Uncomment and configure your analytics service
      /*
      fetch('/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event),
      }).catch(err => console.error('Analytics error:', err));
      */

      // Or use Google Analytics
      /*
      if (window.gtag) {
        window.gtag('event', event.event, event.properties);
      }
      */

      // Or use Plausible
      /*
      if (window.plausible) {
        window.plausible(event.event, { props: event.properties });
      }
      */
    }
  }

  /**
   * Get all tracked events (for debugging)
   */
  getEvents() {
    return this.events;
  }
}

// Export singleton instance
export const analytics = new Analytics();

// Export hook for React components
export function useAnalytics() {
  return analytics;
}
