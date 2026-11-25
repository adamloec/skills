"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { createStore, useStore, type StateCreator, type StoreApi } from "zustand";
import { shallow } from "zustand/shallow";

/** What `seededStore` hands back: the provider that makes the store, and the hooks that read it. */
export interface SeededStore<State, Seed> {
  /** Creates the store from `seed` for everything inside it, and takes each newer seed the server sends. */
  Provider: (props: { seed: Seed; children: ReactNode }) => ReactNode;
  /** Read the store reactively. Pass an atomic selector. */
  useStore: <T = State>(selector?: (state: State) => T) => T;
  /** The store itself, for an imperative read inside a callback. */
  useStoreApi: () => StoreApi<State>;
}

/**
 * Build a store that exists per request and holds its first state before anything renders.
 *
 * @param name - Names the store in the error a hook raises outside its provider.
 * @param build - Builds the whole state from the seed: the seed's own keys, plus any actions.
 * @param take - What a newer seed changes, given the store as it is. Omit to write the seed's
 * keys over the store's. A store that saves something of its own passes this, so a seed read
 * while a save was in flight does not put the old value back.
 */
export function seededStore<State extends Seed, Seed extends object>(
  name: string,
  build: (seed: Seed) => StateCreator<State>,
  take: (state: State, seed: Seed) => Partial<State> = (_state, seed) => seed as Partial<State>,
): SeededStore<State, Seed> {
  const Context = createContext<StoreApi<State> | null>(null);

  function Provider({ seed, children }: { seed: Seed; children: ReactNode }) {
    const [store] = useState(() => createStore<State>()(build(seed)));
    const taken = useRef(seed);
    useEffect(() => {
      if (shallow(taken.current, seed)) return;
      taken.current = seed;
      store.setState(take(store.getState(), seed));
    });
    return <Context.Provider value={store}>{children}</Context.Provider>;
  }

  function useStoreApi(): StoreApi<State> {
    const store = useContext(Context);
    if (!store) throw new Error(`The ${name} store was read outside its provider.`);
    return store;
  }

  function useSeededStore<T = State>(selector?: (state: State) => T): T {
    return useStore(useStoreApi(), selector ?? ((state) => state as unknown as T));
  }

  return { Provider, useStore: useSeededStore, useStoreApi };
}
