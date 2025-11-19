/**
 * Virtual Scrolling List Component
 * Optimized for rendering large lists with minimal DOM nodes
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { throttle } from '../utils/performanceUtils';

const VirtualScrollList = ({
  items = [],
  itemHeight = 50,
  containerHeight = 400,
  renderItem,
  overscan = 5,
  className = '',
  onScroll,
  estimatedItemHeight,
  getItemHeight,
  loadMore,
  hasNextPage = false,
  isLoading = false,
  threshold = 0.8,
  ...props
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const containerRef = useRef(null);
  const scrollTimeoutRef = useRef(null);

  // Calculate dynamic item heights if provided
  const itemHeights = useMemo(() => {
    if (getItemHeight) {
      return items.map((item, index) => getItemHeight(item, index));
    }
    return new Array(items.length).fill(itemHeight);
  }, [items, itemHeight, getItemHeight]);

  // Calculate total height
  const totalHeight = useMemo(() => {
    if (getItemHeight) {
      return itemHeights.reduce((sum, height) => sum + height, 0);
    }
    return items.length * itemHeight;
  }, [items.length, itemHeight, itemHeights, getItemHeight]);

  // Calculate visible range
  const visibleRange = useMemo(() => {
    if (getItemHeight) {
      // Dynamic height calculation
      let startIndex = 0;
      let accumulatedHeight = 0;
      
      for (let i = 0; i < itemHeights.length; i++) {
        if (accumulatedHeight >= scrollTop) {
          startIndex = Math.max(0, i - overscan);
          break;
        }
        accumulatedHeight += itemHeights[i];
      }

      let endIndex = startIndex;
      accumulatedHeight = itemHeights.slice(0, startIndex).reduce((sum, h) => sum + h, 0);
      
      while (endIndex < itemHeights.length && accumulatedHeight < scrollTop + containerHeight) {
        accumulatedHeight += itemHeights[endIndex];
        endIndex++;
      }
      
      endIndex = Math.min(itemHeights.length - 1, endIndex + overscan);
      
      return { startIndex, endIndex };
    } else {
      // Fixed height calculation
      const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
      const endIndex = Math.min(
        items.length - 1,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
      );
      
      return { startIndex, endIndex };
    }
  }, [scrollTop, containerHeight, itemHeight, itemHeights, overscan, items.length, getItemHeight]);

  // Calculate item positions
  const getItemTop = useCallback((index) => {
    if (getItemHeight) {
      return itemHeights.slice(0, index).reduce((sum, height) => sum + height, 0);
    }
    return index * itemHeight;
  }, [itemHeight, itemHeights, getItemHeight]);

  // Throttled scroll handler
  const handleScroll = useCallback(
    throttle((event) => {
      const newScrollTop = event.target.scrollTop;
      setScrollTop(newScrollTop);
      setIsScrolling(true);

      // Clear existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // Set scrolling to false after scroll ends
      scrollTimeoutRef.current = setTimeout(() => {
        setIsScrolling(false);
      }, 150);

      // Call external scroll handler
      if (onScroll) {
        onScroll(event);
      }

      // Infinite scrolling
      if (loadMore && hasNextPage && !isLoading) {
        const scrollPercentage = newScrollTop / (totalHeight - containerHeight);
        if (scrollPercentage >= threshold) {
          loadMore();
        }
      }
    }, 16), // ~60fps
    [onScroll, loadMore, hasNextPage, isLoading, totalHeight, containerHeight, threshold]
  );

  // Render visible items
  const visibleItems = useMemo(() => {
    const items_to_render = [];
    
    for (let i = visibleRange.startIndex; i <= visibleRange.endIndex; i++) {
      if (i >= items.length) break;
      
      const item = items[i];
      const top = getItemTop(i);
      const height = getItemHeight ? itemHeights[i] : itemHeight;
      
      items_to_render.push(
        <div
          key={i}
          style={{
            position: 'absolute',
            top,
            left: 0,
            right: 0,
            height,
            display: 'flex',
            alignItems: 'center'
          }}
          data-index={i}
        >
          {renderItem(item, i, {
            isScrolling,
            isVisible: true
          })}
        </div>
      );
    }
    
    return items_to_render;
  }, [visibleRange, items, getItemTop, itemHeight, itemHeights, getItemHeight, renderItem, isScrolling]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // Loading indicator
  const LoadingIndicator = () => (
    <div className="flex justify-center items-center py-4">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      <span className="ml-2 text-sm text-gray-600">Loading more...</span>
    </div>
  );

  return (
    <div
      ref={containerRef}
      className={`virtual-scroll-container overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
      {...props}
    >
      <div
        className="virtual-scroll-content relative"
        style={{ height: totalHeight }}
      >
        {visibleItems}
        
        {/* Loading indicator for infinite scroll */}
        {isLoading && (
          <div
            style={{
              position: 'absolute',
              top: totalHeight,
              left: 0,
              right: 0,
              height: 60
            }}
          >
            <LoadingIndicator />
          </div>
        )}
      </div>
    </div>
  );
};

// Higher-order component for virtual scrolling
export const withVirtualScrolling = (WrappedComponent) => {
  return React.forwardRef((props, ref) => {
    const {
      items,
      itemHeight = 50,
      containerHeight = 400,
      virtualized = true,
      ...otherProps
    } = props;

    if (!virtualized || items.length < 100) {
      // Render normally for small lists
      return <WrappedComponent {...props} ref={ref} />;
    }

    // Use virtual scrolling for large lists
    return (
      <VirtualScrollList
        items={items}
        itemHeight={itemHeight}
        containerHeight={containerHeight}
        renderItem={(item, index, meta) => (
          <WrappedComponent
            key={index}
            item={item}
            index={index}
            meta={meta}
            {...otherProps}
            ref={ref}
          />
        )}
      />
    );
  });
};

// Hook for virtual scrolling state
export const useVirtualScrolling = (items, options = {}) => {
  const {
    itemHeight = 50,
    containerHeight = 400,
    overscan = 5,
    threshold = 0.8
  } = options;

  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);

  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemHeight, overscan, items.length]);

  const totalHeight = items.length * itemHeight;

  const scrollHandler = useCallback(
    throttle((event) => {
      setScrollTop(event.target.scrollTop);
      setIsScrolling(true);
      
      setTimeout(() => setIsScrolling(false), 150);
    }, 16),
    []
  );

  const getItemStyle = useCallback((index) => ({
    position: 'absolute',
    top: index * itemHeight,
    left: 0,
    right: 0,
    height: itemHeight
  }), [itemHeight]);

  const shouldLoadMore = useCallback((scrollTop) => {
    const scrollPercentage = scrollTop / (totalHeight - containerHeight);
    return scrollPercentage >= threshold;
  }, [totalHeight, containerHeight, threshold]);

  return {
    visibleRange,
    totalHeight,
    scrollHandler,
    getItemStyle,
    shouldLoadMore,
    isScrolling,
    scrollTop
  };
};

// Memoized list item component
export const VirtualListItem = React.memo(({ 
  children, 
  index, 
  style, 
  className = '',
  ...props 
}) => (
  <div
    className={`virtual-list-item ${className}`}
    style={style}
    data-index={index}
    {...props}
  >
    {children}
  </div>
));

VirtualListItem.displayName = 'VirtualListItem';

export default VirtualScrollList;