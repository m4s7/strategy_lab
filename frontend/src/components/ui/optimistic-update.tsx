"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { CheckCircle, XCircle, RefreshCw } from "lucide-react";

interface OptimisticUpdateOptions<T> {
  onUpdate: (data: T) => Promise<T>;
  onSuccess?: (data: T) => void;
  onError?: (error: Error, previousData: T) => void;
  timeout?: number;
}

export function useOptimisticUpdate<T>(
  initialData: T,
  options: OptimisticUpdateOptions<T>
) {
  const [data, setData] = useState<T>(initialData);
  const [status, setStatus] = useState<
    "idle" | "pending" | "success" | "error"
  >("idle");
  const [error, setError] = useState<Error | null>(null);
  const previousDataRef = useRef<T>(initialData);

  const update = useCallback(
    async (newData: T) => {
      // Store previous data for rollback
      previousDataRef.current = data;

      // Optimistically update UI
      setData(newData);
      setStatus("pending");
      setError(null);

      try {
        const result = await options.onUpdate(newData);
        setData(result);
        setStatus("success");
        options.onSuccess?.(result);

        // Reset status after timeout
        if (options.timeout) {
          setTimeout(() => setStatus("idle"), options.timeout);
        }
      } catch (err) {
        // Rollback on error
        setData(previousDataRef.current);
        setStatus("error");
        setError(err as Error);
        options.onError?.(err as Error, previousDataRef.current);

        // Reset status after timeout
        if (options.timeout) {
          setTimeout(() => setStatus("idle"), options.timeout);
        }
      }
    },
    [data, options]
  );

  const retry = useCallback(() => {
    if (error) {
      update(data);
    }
  }, [data, error, update]);

  return {
    data,
    status,
    error,
    update,
    retry,
  };
}

interface OptimisticUpdateIndicatorProps {
  status: "idle" | "pending" | "success" | "error";
  message?: {
    pending?: string;
    success?: string;
    error?: string;
  };
  className?: string;
}

export function OptimisticUpdateIndicator({
  status,
  message = {
    pending: "Saving...",
    success: "Saved!",
    error: "Failed to save",
  },
  className,
}: OptimisticUpdateIndicatorProps) {
  if (status === "idle") return null;

  const icons = {
    pending: <RefreshCw className="w-4 h-4 animate-spin" />,
    success: <CheckCircle className="w-4 h-4" />,
    error: <XCircle className="w-4 h-4" />,
  };

  const colors = {
    pending: "text-muted-foreground",
    success: "text-success",
    error: "text-error",
  };

  return (
    <div
      className={`flex items-center gap-2 text-sm ${colors[status]} ${className}`}
    >
      {icons[status]}
      <span>{message[status]}</span>
    </div>
  );
}

interface OptimisticListOptions<T> {
  keyExtractor: (item: T) => string | number;
  onAdd?: (item: T) => Promise<T>;
  onUpdate?: (item: T) => Promise<T>;
  onDelete?: (id: string | number) => Promise<void>;
  onReorder?: (items: T[]) => Promise<T[]>;
}

export function useOptimisticList<T>(
  initialItems: T[],
  options: OptimisticListOptions<T>
) {
  const [items, setItems] = useState<T[]>(initialItems);
  const [pendingActions, setPendingActions] = useState<Set<string>>(new Set());
  const previousItemsRef = useRef<T[]>(initialItems);

  const addItem = useCallback(
    async (item: T) => {
      const id = options.keyExtractor(item);
      previousItemsRef.current = items;

      // Optimistically add
      setItems((prev) => [...prev, item]);
      setPendingActions((prev) => new Set(prev).add(`add-${id}`));

      try {
        if (options.onAdd) {
          const result = await options.onAdd(item);
          setItems((prev) =>
            prev.map((i) => (options.keyExtractor(i) === id ? result : i))
          );
        }
      } catch (error) {
        // Rollback
        setItems(previousItemsRef.current);
        throw error;
      } finally {
        setPendingActions((prev) => {
          const next = new Set(prev);
          next.delete(`add-${id}`);
          return next;
        });
      }
    },
    [items, options]
  );

  const updateItem = useCallback(
    async (item: T) => {
      const id = options.keyExtractor(item);
      previousItemsRef.current = items;

      // Optimistically update
      setItems((prev) =>
        prev.map((i) => (options.keyExtractor(i) === id ? item : i))
      );
      setPendingActions((prev) => new Set(prev).add(`update-${id}`));

      try {
        if (options.onUpdate) {
          const result = await options.onUpdate(item);
          setItems((prev) =>
            prev.map((i) => (options.keyExtractor(i) === id ? result : i))
          );
        }
      } catch (error) {
        // Rollback
        setItems(previousItemsRef.current);
        throw error;
      } finally {
        setPendingActions((prev) => {
          const next = new Set(prev);
          next.delete(`update-${id}`);
          return next;
        });
      }
    },
    [items, options]
  );

  const deleteItem = useCallback(
    async (id: string | number) => {
      previousItemsRef.current = items;

      // Optimistically delete
      setItems((prev) => prev.filter((i) => options.keyExtractor(i) !== id));
      setPendingActions((prev) => new Set(prev).add(`delete-${id}`));

      try {
        if (options.onDelete) {
          await options.onDelete(id);
        }
      } catch (error) {
        // Rollback
        setItems(previousItemsRef.current);
        throw error;
      } finally {
        setPendingActions((prev) => {
          const next = new Set(prev);
          next.delete(`delete-${id}`);
          return next;
        });
      }
    },
    [items, options]
  );

  const reorderItems = useCallback(
    async (newOrder: T[]) => {
      previousItemsRef.current = items;

      // Optimistically reorder
      setItems(newOrder);
      setPendingActions((prev) => new Set(prev).add("reorder"));

      try {
        if (options.onReorder) {
          const result = await options.onReorder(newOrder);
          setItems(result);
        }
      } catch (error) {
        // Rollback
        setItems(previousItemsRef.current);
        throw error;
      } finally {
        setPendingActions((prev) => {
          const next = new Set(prev);
          next.delete("reorder");
          return next;
        });
      }
    },
    [items, options]
  );

  const isPending = useCallback(
    (action: string, id?: string | number) => {
      if (id !== undefined) {
        return pendingActions.has(`${action}-${id}`);
      }
      return pendingActions.has(action);
    },
    [pendingActions]
  );

  return {
    items,
    addItem,
    updateItem,
    deleteItem,
    reorderItems,
    isPending,
    isAnyPending: pendingActions.size > 0,
  };
}
