import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Copy, 
  Edit, 
  Trash2, 
  Eye, 
  EyeOff, 
  Star, 
  StarOff,
  Download,
  Share,
  Settings,
  MoreHorizontal,
  ChevronRight
} from 'lucide-react';

const ContextMenu = ({ 
  isOpen, 
  position, 
  onClose, 
  items = [], 
  target = null 
}) => {
  const menuRef = useRef(null);
  const [submenuOpen, setSubmenuOpen] = useState(null);
  const [menuPosition, setMenuPosition] = useState(position);

  // Закрытие меню при клике вне его
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };

    const handleScroll = () => {
      onClose();
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('scroll', handleScroll, true);
      
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('scroll', handleScroll, true);
      };
    }
  }, [isOpen, onClose]);

  // Корректировка позиции меню для предотвращения выхода за границы экрана
  useEffect(() => {
    if (isOpen && menuRef.current && position) {
      const menu = menuRef.current;
      const rect = menu.getBoundingClientRect();
      const viewport = {
        width: window.innerWidth,
        height: window.innerHeight
      };

      let { x, y } = position;

      // Корректировка по горизонтали
      if (x + rect.width > viewport.width) {
        x = viewport.width - rect.width - 10;
      }
      if (x < 10) {
        x = 10;
      }

      // Корректировка по вертикали
      if (y + rect.height > viewport.height) {
        y = viewport.height - rect.height - 10;
      }
      if (y < 10) {
        y = 10;
      }

      setMenuPosition({ x, y });
    }
  }, [isOpen, position]);

  // Обработка клавиатуры
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (!isOpen) return;

      switch (event.key) {
        case 'Escape':
          event.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleItemClick = (item, event) => {
    event.stopPropagation();
    
    if (item.submenu) {
      setSubmenuOpen(submenuOpen === item.id ? null : item.id);
      return;
    }

    if (item.action) {
      item.action(target, event);
    }
    
    if (!item.keepOpen) {
      onClose();
    }
  };

  const renderIcon = (icon) => {
    if (typeof icon === 'string') {
      // Предустановленные иконки
      const iconMap = {
        copy: Copy,
        edit: Edit,
        delete: Trash2,
        view: Eye,
        hide: EyeOff,
        star: Star,
        unstar: StarOff,
        download: Download,
        share: Share,
        settings: Settings,
        more: MoreHorizontal
      };
      const IconComponent = iconMap[icon];
      return IconComponent ? <IconComponent className="h-4 w-4" /> : null;
    }
    
    if (React.isValidElement(icon)) {
      return icon;
    }
    
    return null;
  };

  const renderMenuItem = (item, index) => {
    const hasSubmenu = item.submenu && item.submenu.length > 0;
    const isSubmenuOpen = submenuOpen === item.id;
    const isDisabled = item.disabled;
    const isDangerous = item.danger;

    return (
      <div key={item.id || index} className="relative">
        <button
          onClick={(e) => handleItemClick(item, e)}
          disabled={isDisabled}
          className={`w-full px-3 py-2 text-left flex items-center space-x-3 transition-colors ${
            isDisabled
              ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
              : isDangerous
              ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          } ${
            isSubmenuOpen ? 'bg-gray-100 dark:bg-gray-700' : ''
          }`}
        >
          {item.icon && (
            <div className="flex-shrink-0">
              {renderIcon(item.icon)}
            </div>
          )}
          
          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">
              {item.label}
            </div>
            {item.description && (
              <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {item.description}
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2 flex-shrink-0">
            {item.shortcut && (
              <kbd className="px-1.5 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 rounded">
                {item.shortcut}
              </kbd>
            )}
            {hasSubmenu && (
              <ChevronRight className="h-4 w-4 text-gray-400" />
            )}
          </div>
        </button>

        {/* Submenu */}
        <AnimatePresence>
          {hasSubmenu && isSubmenuOpen && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              className="absolute left-full top-0 ml-1 min-w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-10"
            >
              {item.submenu.map((subItem, subIndex) => (
                <button
                  key={subItem.id || subIndex}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (subItem.action) {
                      subItem.action(target, e);
                    }
                    if (!subItem.keepOpen) {
                      onClose();
                    }
                  }}
                  disabled={subItem.disabled}
                  className={`w-full px-3 py-2 text-left flex items-center space-x-3 transition-colors ${
                    subItem.disabled
                      ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
                      : subItem.danger
                      ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  {subItem.icon && (
                    <div className="flex-shrink-0">
                      {renderIcon(subItem.icon)}
                    </div>
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      {subItem.label}
                    </div>
                    {subItem.description && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {subItem.description}
                      </div>
                    )}
                  </div>
                  
                  {subItem.shortcut && (
                    <kbd className="px-1.5 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 rounded">
                      {subItem.shortcut}
                    </kbd>
                  )}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  const renderSeparator = (index) => (
    <div key={`separator-${index}`} className="my-1 border-t border-gray-200 dark:border-gray-700" />
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={menuRef}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.15 }}
          className="fixed z-50 min-w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1"
          style={{
            left: menuPosition?.x || 0,
            top: menuPosition?.y || 0,
          }}
        >
          {items.map((item, index) => {
            if (item.type === 'separator') {
              return renderSeparator(index);
            }
            return renderMenuItem(item, index);
          })}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Hook для использования контекстного меню
export const useContextMenu = () => {
  const [contextMenu, setContextMenu] = useState({
    isOpen: false,
    position: { x: 0, y: 0 },
    items: [],
    target: null
  });

  const showContextMenu = (event, items, target = null) => {
    event.preventDefault();
    event.stopPropagation();
    
    setContextMenu({
      isOpen: true,
      position: { x: event.clientX, y: event.clientY },
      items,
      target
    });
  };

  const hideContextMenu = () => {
    setContextMenu(prev => ({ ...prev, isOpen: false }));
  };

  const ContextMenuComponent = () => (
    <ContextMenu
      isOpen={contextMenu.isOpen}
      position={contextMenu.position}
      items={contextMenu.items}
      target={contextMenu.target}
      onClose={hideContextMenu}
    />
  );

  return {
    showContextMenu,
    hideContextMenu,
    ContextMenuComponent
  };
};

export default ContextMenu;