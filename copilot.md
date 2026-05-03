# Observations and Recommendations

## DataBus: Future-Ready Recommendations

1. **Improve DataBus Readership:**
   - Refactor components to directly consume variables from DataBus instead of relying heavily on props. This will enforce its role as a centralized state.
     ```javascript
     const { bus } = useDataBus();
     const visibleInvestments = bus.visibleInvestments || [];
     ```

2. **Scoped Namespaces:**
   - Use namespaces in variables to prevent key collisions and better organize the state.
     ```javascript
     setVariable('filters.investments', { developer: 'XYZ', status: 'Active' });
     const filters = bus.filters?.investments;
     ```

3. **Introduce Asynchronous Dispatchers:**
   - Extend `setVariable` to handle async reducers to allow dynamic fetch-and-set operations.
     ```javascript
     const actions = {
       fetchReports: async () => {
         const reports = await fetch('/api/reports').then((r) => r.json());
         setVariable('reports', reports);
       };
     };
     ```

4. **DevTools Compatibility:**
   - Log state updates to debug data flow easily.
     ```javascript
     const debugVariableChange = (prev, next, name) => console.log(`Variable ${name} changed:`, prev, '→', next);
     ```

---

## Module System: Scalability Improvements

1. **Dynamic Module Registry:**
   - Register modules dynamically with a registry for runtime extensibility.
     ```javascript
     const ModuleRegistry = new Map();

     const registerModule = (type, component) => {
       ModuleRegistry.set(type, component);
     };

     const getRegisteredComponent = (type) => {
       return ModuleRegistry.has(type)
         ? ModuleRegistry.get(type)
         : () => <div>Unknown Module: {type}</div>;
     };

     registerModule('map', MapModule);
     ```

2. **Encapsulate Module Context Logic:**
   - Replace repetitive validation logic with a shared `useModuleContext` hook.
     ```javascript
     const useModuleContext = (schema, data) => {
       const validationResults = validate(schema, data);
       return validationResults.valid ? validationResults.aliasedData : null;
     };
     ```

3. **Support Chained Modules:**
   - Enable modules to provide context for child modules, e.g., hierarchical visualizations.
     ```javascript
     <ModuleWrapper>
        <PriceTrendModule config={trendConfig}>
           <BarChart dataKey="aggregatedPriceDistribution" />
        </PriceTrendModule>
     </ModuleWrapper>
     ```

4. **Standardize Module Specs:**
   - Define a JSON-based module specification to manage inputs and outputs systematically.
     ```json
     {
       "modules": [
         { "id": "price", "type": "PriceTrendModule", "config": { "highlight": "Warsaw" } },
         { "id": "map", "type": "MapModule", "config": { "dark": true } }
       ]
     }
     ```

---

## Refactor Suggestions

1. **Streamline `components.jsx`:**
   - Break down the 742 lines into smaller files:
     - `components/core.jsx`: UI primitives like `Spinner`, `Icon`.
     - `components/ratings.jsx`: Star Rating and rating components.
     - `components/modules.jsx`: `ModuleWrapper`, `BaseModule`.

2. **Consolidate Duplicate Logic:**
   - Simplify repeated rating logic between `CategoryRating`, `ocenaLog`, and `avgRating`.

3. **Refactor Views with Shared Grids:**
   - Abstract shared grid logic from `view-reports` and `view-dashboard` into reusable `DataGrid` components.

4. **Centralize API Fetching:**
   - Move repetitive `fetch` calls (in `useInvestments`, `useReports`, etc.) into a single query client.
     ```javascript
     const useApi = (endpoint) => {
       const [data, setData] = React.useState(null);
       React.useEffect(() => {
         fetch(endpoint).then((resp) => resp.json()).then(setData);
       }, [endpoint]);
       return data;
     };
     ```

---

## Long-Term Considerations

1. **DataBus Subscriptions:**
   - Introduce event-driven subscriptions for components to reactively update based on specific state changes.

2. **Consider Redux Toolkit:**
   - Evaluate replacing DataBus with Redux Toolkit for built-in devtools, middleware, and better scalability in complex state management.

3. **Test Module Isolation:**
   - Implement Storybook tests for individual modules such as `TableModule` and `RatingComparisonModule` to ensure reusability.

---

By implementing these improvements, the DataBus and Module System can grow into robust and scalable solutions for managing application state and dynamic rendering.