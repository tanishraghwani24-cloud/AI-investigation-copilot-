import '@testing-library/jest-dom';

/**
 * jsdom does not implement IntersectionObserver, which Motion's `whileInView`
 * (used by the landing page scroll reveals) constructs on mount. Without this
 * stub any render of a page containing them throws "IntersectionObserver is
 * not defined". Observed elements are simply never reported as intersecting,
 * so reveals stay in their initial state — text stays in the DOM either way,
 * which is all the queries care about.
 */
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: ReadonlyArray<number> = [];

  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

global.IntersectionObserver = MockIntersectionObserver as unknown as typeof IntersectionObserver;
