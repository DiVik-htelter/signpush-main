import React, { createContext, useState } from 'react';

export const SidebarContext = createContext();

export function SidebarProvider({ children }) {
    const [isCollapsed, setIsCollapsed] = useState(false);

    return (
        <SidebarContext.Provider value={{ isCollapsed, setIsCollapsed }}>
            {children}
        </SidebarContext.Provider>
    );
}
