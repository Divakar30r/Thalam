import React, { Fragment, useState, useEffect, useMemo, useCallback } from 'react';
import { INDUSTRY_DATA as MOCK_INDUSTRY_DATA } from '@/utils/mocks/mock-data';
import { Dialog, Transition } from '@headlessui/react';
import Welcome from '@/pages/Welcome';
import Login from '@/pages/Login';

// --- TYPE DEFINITIONS ---
interface Product {
  id: number;
  productName: string;
  quantity: string;
  remarks: string;
  factors: Record<string, any>;
}

interface Industry {
  Industry: string;
  Scale: string;
  // rename to factorskey to differentiate role-details metadata vs product.factors
  factorskey: Record<string, any>;
}

// --- API CONFIG ---
import { API_BASE_URL, PRESIGNED_URL_CONFIG_NAME, PRESIGNED_URL_ENDPOINT, PRESIGNED_STATUS_ENDPOINT, PRESIGNED_DOCS_ENDPOINT, PRESIGNED_PUBLIC_URL_ENDPOINT, PRESIGNED_ATTACH_ENDPOINT } from '@/config';

// --- HELPER FUNCTIONS ---
import { parseISO } from 'date-fns';
const isRequired = (key: string) => key.endsWith('*');
const hasValueInput = (key: string) => key.startsWith('^');
const getLabel = (key: string) => key.replace(/[*^]/g, '');

const formatFactorValue = (value) => {
    if (!value) return 'N/A';
    if (typeof value === 'object' && value !== null) {
        if (value.value || value.unit) {
            return `${value.value || ''} ${value.unit || ''}`.trim() || 'N/A';
        }
    }
    if (Array.isArray(value) && value.length > 0) {
        return value.join(', ');
    }
     if (Array.isArray(value) && value.length === 0) {
        return 'N/A';
    }
    return String(value);
};

// normalize industry objects returned from the backend into our local shape
const normalizeIndustry = (raw: any): Industry | null => {
  if (!raw) return null;
  // backend likely uses `factors` property; map it to `factorskey`
  const { Industry: name, Scale, factors } = raw as any;
  return {
    Industry: name || raw?.Industry || '',
    Scale: Scale || raw?.Scale || '',
    factorskey: factors || raw?.factors || {},
  } as Industry;
};


// --- DYNAMIC FORM FIELD COMPONENT ---
interface FactorFieldProps {
  factorKey: string;
  factorValue: any;
  value: any;
  onChange: (factorKey: string, value: any) => void;
  readOnly?: boolean;
  invalid?: boolean;
}

const FactorField: React.FC<FactorFieldProps> = ({ factorKey, factorValue, value, onChange, readOnly = false, invalid = false }) => {
  const label = getLabel(factorKey);
  const required = isRequired(factorKey);

  if (readOnly) {
    return (
         <div>
            <p className="mt-1 block w-full pl-3 py-2 text-sm text-gray-700 bg-gray-100 border border-gray-200 rounded-md">
                <span className="font-medium text-gray-500">{label}:</span> {formatFactorValue(value)}
            </p>
        </div>
    );
  }

    const handleMultiSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedOptions = Array.from(e.target.selectedOptions, (option: HTMLOptionElement) => option.value);
    onChange(factorKey, selectedOptions);
  };

  // Type 0: Key with '^' prefix -> Text Input + Select Dropdown
  if (hasValueInput(factorKey)) {
    const unitValue = value?.unit || '';
    const textValue = value?.value || '';
    const isValueRequired = required || !!unitValue;

    const handleUnitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChange(factorKey, { unit: e.target.value, value: textValue });
    };

    const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(factorKey, { unit: unitValue, value: e.target.value });
    };

    return (
       <div>
            <div className="flex items-center space-x-2 mt-1">
        {unitValue && (
          <input
            type="text"
            id={`${factorKey}-value`}
            name={`${factorKey}-value`}
            required={isValueRequired}
            value={textValue}
            onChange={handleTextChange}
            className={`block w-1/2 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${invalid ? 'border-red-500 ring-1 ring-red-200' : 'border-gray-300'}`}
            placeholder="Value"
          />
        )}
                <select
                    id={`${factorKey}-unit`}
                    name={`${factorKey}-unit`}
                    value={unitValue}
                    onChange={handleUnitChange}
          className={`block ${!unitValue ? 'w-full' : 'w-1/2'} pl-3 pr-10 py-2 text-base focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md ${invalid ? 'border-red-500 ring-1 ring-red-200' : 'border-gray-300'}`}
                >
                    <option value="">{label}? {required && '*'}</option>
                    {(factorValue as string[]).map(option => <option key={option} value={option}>{option}</option>)}
                </select>
            </div>
        </div>
    );
  }


  // Type 1: Multi-select from '*/*' separated string
  if (typeof factorValue === 'string' && factorValue.includes('*/*')) {
    const options = factorValue.split('*/*').filter(Boolean);
    return (
      <div>
        <select
          id={factorKey}
          name={factorKey}
          multiple
          required={required}
          value={value || []}
          onChange={handleMultiSelectChange}
          className={`mt-1 block w-full pl-3 pr-10 py-2 text-base focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md ${invalid ? 'border-red-500 ring-1 ring-red-200' : 'border-gray-300'}`}
        >
          <option value="" disabled>{label}? (multi-select) {required && '*'}</option>
          {options.map(option => <option key={option} value={option}>{option}</option>)}
        </select>
      </div>
    );
  }

  // Type 2: Simple string -> single-option dropdown
  if (typeof factorValue === 'string') {
      return (
        <div>
          <select
            id={factorKey}
            name={factorKey}
            required={required}
            value={value || ''}
            onChange={(e) => onChange(factorKey, e.target.value)}
            className={`mt-1 block w-full pl-3 pr-10 py-2 text-base focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md ${invalid ? 'border-red-500 ring-1 ring-red-200' : 'border-gray-300'}`}
          >
            <option value="">{label}? {required && '*'}</option>
            <option key={factorValue} value={factorValue}>{factorValue}</option>
          </select>
        </div>
      );
  }

  // Type 3: Array with only one item AND it's required -> read-only display, auto-selected
  if (Array.isArray(factorValue) && factorValue.length === 1 && required) {
    const singleValue = factorValue[0];

  useEffect(() => {
    if (value !== singleValue) {
      onChange(factorKey, singleValue);
    }
  }, [factorKey, singleValue, value, onChange]);

    return (
        <div>
      <p className="mt-1 block w-full pl-3 py-2 text-sm text-gray-600 bg-gray-100 border border-gray-300 rounded-md">
        <span className="font-medium">{label}:</span> {singleValue}
      </p>
        </div>
    );
  }

  // Type 4: Simple array (including single-item optional) -> single-select dropdown
  if (Array.isArray(factorValue)) {
    return (
      <div>
        <select
          id={factorKey}
          name={factorKey}
          required={required}
          value={value || ''}
          onChange={(e) => onChange(factorKey, e.target.value)}
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          <option value="">{label}? {required && '*'}</option>
          {factorValue.map(option => <option key={option} value={option}>{option}</option>)}
        </select>
      </div>
    );
  }

  // Type 5: Object with arrays -> dropdown with optgroup
  if (typeof factorValue === 'object' && factorValue !== null) {
    return (
      <div>
        <select
          id={factorKey}
          name={factorKey}
          required={required}
          value={value || ''}
          onChange={(e) => onChange(factorKey, e.target.value)}
          className={`mt-1 block w-full pl-3 pr-10 py-2 text-base focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md ${invalid ? 'border-red-500 ring-1 ring-red-200' : 'border-gray-300'}`}
        >
          <option value="">{label}? {required && '*'}</option>
          {Object.entries(factorValue).map(([groupLabel, options]) => (
            <optgroup key={groupLabel} label={groupLabel}>
              {(options as string[]).map(option => <option key={option} value={option}>{option}</option>)}
            </optgroup>
          ))}
        </select>
      </div>
    );
  }

  return null;
};


// --- EDIT FRAME (MODAL or INLINE) COMPONENT ---
// Supports `inline` prop. When inline=true the editor renders as a right-side panel
// instead of a modal overlay.
const EditFrame = ({ industry, product, onSave, onClose, readOnly = false, title = '', inline = false, validateForSave }: any) => {
  const [formData, setFormData] = useState<Partial<Product>>(product);
  const [hasTouchedName, setHasTouchedName] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  // track which factor keys are invalid for UI highlight
  const [invalidFactors, setInvalidFactors] = useState<Record<string, boolean>>({});

  // helper: produce an empty/default value for a factor definition
  const defaultValueForFactorDef = useCallback((key: string, def: any) => {
    // key may start with '^' meaning value+unit
    if (hasValueInput(key)) {
      return { unit: '', value: '' };
    }
    // multi-select encoded as '*/*' string
    if (typeof def === 'string' && def.includes('*/*')) return [];
    // arrays -> single-select default empty string
    if (Array.isArray(def)) return '';
    // object (optgroups) -> empty string
    if (typeof def === 'object' && def !== null) return '';
    // fallback
    return '';
  }, []);

  // When product or industry changes, initialize formData with a full set of factor keys
  useEffect(() => {
    // start with shallow copy of product
    const base: Partial<Product> = { ...(product || {}) };
    // ensure factors object exists
    const mergedFactors: Record<string, any> = {};
    try {
      const factorDefs = industry?.factorskey || {};
      // for each factor key defined by the industry, prefer product value if present
      Object.entries(factorDefs).forEach(([k, def]) => {
        const prodVal = product?.factors?.[k];
        if (prodVal !== undefined && prodVal !== null) {
          // if product value is present, use it directly
          mergedFactors[k] = prodVal;
        } else {
          // otherwise use an appropriate default so the FactorField can render
          mergedFactors[k] = defaultValueForFactorDef(k, def);
        }
      });
    } catch (err) {
      // fallback: copy whatever product had
      Object.assign(mergedFactors, product?.factors || {});
    }

    base.factors = mergedFactors;
    // debug: show merged state so we can verify that industry factor keys and any
    // loaded product values were merged correctly. Open browser console to inspect.
    try {
      console.log('EditFrame:init', { industry: industry?.Industry, factorDefs: industry?.factors, product, mergedFactors, formDataPreview: base });
    } catch (err) {
      // ignore console errors in older browsers
    }
    setFormData(base);
    setInvalidFactors({});
  }, [product, industry, defaultValueForFactorDef]);

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleFactorChange = (factorKey: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      factors: {
        ...prev.factors,
        [factorKey]: value,
      },
    }));
    // clear invalid flag for this factor as user modified it
    setInvalidFactors(prev => ({ ...prev, [factorKey]: false }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  if (!industry) return null;

  const modalTitle = title || `Add/Edit for ${industry.Industry}`;
  // build the form once so we can render it inside a modal or inline panel
  const formElement = (
    <form onSubmit={handleSubmit}>
      <div className="px-6 py-4 border-b flex justify-between items-center">
        <h3 className="text-xl font-semibold text-gray-800">{modalTitle}</h3>
          {inline && (
          <button type="button" aria-label="Close" onClick={() => {
            // Only require productName when closing the inline editor.
            // Preferences and remarks are optional at this stage and will be
            // validated at final submit time (Submit Order).
            if (!formData.productName || !formData.productName.trim()) {
              // nothing to save, just close
              setValidationError(null);
              setInvalidFactors({});
              onClose();
              return;
            }

            // validate using parent-supplied function if available
            const validator = validateForSave || (() => ({ ok: true }));
            const validation = validator(formData);
            if (!validation?.ok) {
              setValidationError(validation?.message || 'Please complete required fields before saving.');
              return;
            }

            // reset validation UI
            setValidationError(null);
            setInvalidFactors({});

            // Console log the editing product object before saving (include sequence id if present)
            try { console.log('editingProduct:onClose', { ...formData }); } catch (err) {}

            // Save the product (this will POST/PUT the order as Draft) and close.
            onSave(formData, { close: true });
          }} className="text-gray-500 hover:text-gray-800">✕</button>
        )}
      </div>
      <div className="p-6 space-y-4 overflow-y-auto" style={{maxHeight: '70vh'}}>
        {validationError && (
          <div className="bg-red-50 border-l-4 border-red-400 text-red-700 p-3 rounded mb-2">
            <strong className="font-semibold">Validation:</strong> {validationError}
          </div>
        )}
        {/* --- Static Fields --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="productName" className="block text-sm font-medium text-gray-700">Product Name <span className="text-red-500">*</span></label>
            <input
              type="text"
              id="productName"
              name="productName"
              required
              disabled={readOnly}
              value={formData.productName || ''}
              onChange={(e) => {
                const val = e.target.value;
                setHasTouchedName(true);
                handleChange('productName', val);
                // Auto-save once productName is non-empty
                if (val && val.trim()) {
                  onSave({ ...formData, productName: val });
                }
              }}
              className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 ${hasTouchedName && (!formData.productName || !formData.productName.trim()) ? 'border-red-500 ring-1 ring-red-200' : 'border-gray-300'}`}
            />
          </div>
          {/* Render quantity in the second column only after productName is present */}
          {(formData.productName && formData.productName.trim()) && (
            <div>
              <label htmlFor="quantity" className="block text-sm font-medium text-gray-700">Quantity</label>
              <input
                type="text"
                id="quantity"
                name="quantity"
                disabled={readOnly}
                value={formData.quantity || ''}
                onChange={(e) => { handleChange('quantity', e.target.value); onSave({ ...formData, quantity: e.target.value }); }}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
              />
            </div>
          )}
        </div>

        {/* Render remarks + preferences only after Product Name is present */}
        {(formData.productName && formData.productName.trim()) && (
          <>
            <div className="mt-4">
              <label htmlFor="remarks" className="block text-sm font-medium text-gray-700">Remarks</label>
              <textarea
                id="remarks"
                name="remarks"
                rows={2}
                disabled={readOnly}
                value={formData.remarks || ''}
                onChange={(e) => { handleChange('remarks', e.target.value); onSave({ ...formData, remarks: e.target.value }); }}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
              ></textarea>
            </div>

            <div className="pt-4 border-t">
              <h4 className="text-lg font-medium text-gray-900 mb-2">Preferences</h4>
              <div className="space-y-4">
                {Object.entries(industry.factorskey || {}).map(([key, valueDef]) => {
                  // value: always reflect the live editing state in formData.factors
                  const initialValue = formData.factors?.[key] ?? (product?.factors && (product.factors[key] !== undefined && product.factors[key] !== null) ? product.factors[key] : undefined);
                  return (
                    <div key={key} className="">
                      <label className="block text-sm font-medium text-gray-700">{getLabel(key)}{isRequired(key) ? ' *' : ''}</label>
                      <div className="mt-1">
                        <FactorField
                          factorKey={key}
                          factorValue={valueDef}
                          value={initialValue}
                          onChange={handleFactorChange}
                          readOnly={readOnly}
                          invalid={!!invalidFactors[key]}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
      {!readOnly && !inline && (
        <div className="bg-gray-50 px-6 py-3 flex justify-end space-x-3">
          <button type="button" onClick={onClose} className="py-2 px-4 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none">
            Cancel
          </button>
          <button type="submit" className="py-2 px-4 bg-indigo-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none">
            Save Product
          </button>
        </div>
      )}
    </form>
  );

  if (inline) {
    return (
      <div className="bg-white rounded-lg shadow-xl w-full">
        {formElement}
      </div>
    );
  }

  // Modal using Headless UI Dialog for accessibility and transitions
  return (
    <Transition appear show as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-0 text-left align-middle shadow-xl transition-all">
                {formElement}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

// --- PROPOSAL WORKFLOW COMPONENTS ---

const getFactorAsString = (factorKey, factorDef, productVal) => {
    if (!productVal) return '';

    if (typeof productVal === 'object' && productVal !== null && 'value' in productVal) {
        return `${productVal.value || ''} ${productVal.unit || ''}`.trim();
    }
    if (Array.isArray(productVal)) {
        return productVal.join(', ');
    }
    if (typeof factorDef === 'object' && factorDef !== null && !Array.isArray(factorDef)) {
        for (const group in factorDef) {
            if ((factorDef[group] as string[]).includes(productVal)) {
                return `${group}: ${productVal}`;
            }
        }
    }
    return String(productVal);
};

const PackingFrame = () => {
    const [packingOrders, setPackingOrders] = useState([]);
    const [currentOrder, setCurrentOrder] = useState({ id: '', packingOrderId: '', packingConstraints: '', fragile: false, volume: '', weight: '' });

    const handleChange = (field, value) => {
        setCurrentOrder(prev => ({ ...prev, [field]: value }));
    };

    const handleAddOrder = (e) => {
        e.preventDefault();
        if (!currentOrder.packingOrderId) {
            alert("Packing Order ID is required.");
            return;
        }
        setPackingOrders(prev => [...prev, { ...currentOrder, id: Date.now() }]);
        setCurrentOrder({ id: '', packingOrderId: '', packingConstraints: '', fragile: false, volume: '', weight: '' }); // Reset form
    };

    return (
        <>
            {/* Top Pane: List */}
            <div className="p-4">
                <h4 className="text-lg font-medium text-gray-900 mb-2">Packing Order List</h4>
                {packingOrders.length > 0 ? (
                    <ul className="divide-y divide-gray-200 border rounded-md max-h-48 overflow-y-auto">
                        {packingOrders.map(order => (
                            <li key={order.id} className="p-3 text-sm">
                                <span className="font-semibold">ID: {order.packingOrderId}</span> | Vol: {order.volume || 'N/A'} | Wt: {order.weight || 'N/A'} | Fragile: {order.fragile ? 'Yes' : 'No'}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-500 text-center py-4">No packing orders added yet.</p>
                )}
            </div>

            {/* Bottom Pane: Form */}
            <form onSubmit={handleAddOrder} className="p-4 pt-4 border-t space-y-4">
                <h4 className="text-lg font-medium text-gray-900">Add New Packing Order</h4>
                <div className="space-y-3">
                     <div>
                        <label className="block text-sm font-medium">Packing Order ID <span className="text-red-500">*</span></label>
                        <input type="text" required value={currentOrder.packingOrderId} onChange={e => handleChange('packingOrderId', e.target.value)} className="mt-1 w-full border-gray-300 rounded-md shadow-sm p-2 text-sm"/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium">Packing Constraints</label>
                        <input type="text" value={currentOrder.packingConstraints} onChange={e => handleChange('packingConstraints', e.target.value)} className="mt-1 w-full border-gray-300 rounded-md shadow-sm p-2 text-sm"/>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                         <div>
                            <label className="block text-sm font-medium">Volume</label>
                            <input type="text" value={currentOrder.volume} onChange={e => handleChange('volume', e.target.value)} className="mt-1 w-full border-gray-300 rounded-md shadow-sm p-2 text-sm"/>
                        </div>
                         <div>
                            <label className="block text-sm font-medium">Weight</label>
                            <input type="text" value={currentOrder.weight} onChange={e => handleChange('weight', e.target.value)} className="mt-1 w-full border-gray-300 rounded-md shadow-sm p-2 text-sm"/>
                        </div>
                    </div>
                    <div>
                        <label className="flex items-center space-x-2">
                            <input type="checkbox" checked={currentOrder.fragile} onChange={e => handleChange('fragile', e.target.checked)} className="rounded"/>
                            <span className="text-sm">Fragile</span>
                        </label>
                    </div>
                </div>
                <div className="flex justify-end">
                    <button type="submit" className="py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm">Add to List</button>
                </div>
            </form>
        </>
    );
};



// --- MAIN APP COMPONENT ---
const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null); // null = checking, false = not auth, true = auth
  const [showApp, setShowApp] = useState(false);
  const [industries, setIndustries] = useState<string[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<Industry | null>(null);
  const [products, setProducts] = useState<Record<string, Product[]>>({});
  const [editingProduct, setEditingProduct] = useState<Partial<Product> | null>(null);
  // internal sequence for product IDs
  const [productSeq, setProductSeq] = useState<number>(1);
  const [orderReqId, setOrderReqId] = useState<string | number | null>(null);
  const [proposingProduct, setProposingProduct] = useState<Product | null>(null);
  const [expectedDeliveryDate, setExpectedDeliveryDate] = useState<string>('');
  const [apiError, setApiError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deliveryDateError, setDeliveryDateError] = useState<string | null>(null);
  // Current logged-in user (assumed available from auth in real app)
  const [currentUserEmail, setCurrentUserEmail] = useState<string>('sb.user1@drworkplace.microsoft.com');
  // If multiple pending drafts exist, block creation
  const [blockedPendingMultiple, setBlockedPendingMultiple] = useState<boolean>(false);
  // Split pane state (left panel width percentage)
  const [leftWidth, setLeftWidth] = useState<number>(25);
  const [isDragging, setIsDragging] = useState(false);
  // Documents list
  const [documents, setDocuments] = useState<any[]>([]);
  const [draftDocuments, setDraftDocuments] = useState<any[]>([]);
  // Collapsible state
  const [isOrderDocsOpen, setIsOrderDocsOpen] = useState(true);
  const [isDraftDocsOpen, setIsDraftDocsOpen] = useState(true);
  // Selected draft documents for attach
  const [selectedDraftDocs, setSelectedDraftDocs] = useState<Set<string>>(new Set());

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // include credentials so cookies set by auth backend (HttpOnly) are sent
        const resp = await fetch('/auth/me', { credentials: 'include' });
        if (resp.ok) {
          const data = await resp.json();
          setIsAuthenticated(true);
          // Set current user email from auth
          if (data.user?.username) {
            setCurrentUserEmail(data.user.username);
          }
        } else {
          setIsAuthenticated(false);
        }
      } catch (err) {
        console.error('Auth check failed:', err);
        setIsAuthenticated(false);
      }
    };
    checkAuth();
  }, []);

  // Fetch documents for the current order
  const fetchDocuments = useCallback(async () => {
    console.log('[fetchDocuments] Called with:', { orderReqId, currentUserEmail });

    if (!orderReqId || !currentUserEmail) {
      console.log('[fetchDocuments] Skipped - missing orderReqId or currentUserEmail');
      return;
    }

    try {
      const params = new URLSearchParams({
        userEmail: currentUserEmail,
        orderReqId: String(orderReqId),
      });
      const url = `${PRESIGNED_DOCS_ENDPOINT}?${params.toString()}`;
      console.log('[fetchDocuments] Fetching:', url);

      const resp = await fetch(url, {
        credentials: 'include',
      });

      console.log('[fetchDocuments] Response status:', resp.status);

      if (!resp.ok) {
        console.warn('[fetchDocuments] Failed to fetch documents:', resp.status);
        return;
      }

      const data = await resp.json();
      console.log('[fetchDocuments] Response data:', data);

      const docs = data?.documents || [];
      console.log('[fetchDocuments] Total documents:', docs.length);

      setDocuments(docs);
    } catch (err) {
      console.error('[fetchDocuments] Error fetching documents:', err);
    }
  }, [orderReqId, currentUserEmail]);

  // Fetch documents when orderReqId changes
  useEffect(() => {
    if (orderReqId) {
      fetchDocuments();
    }
  }, [orderReqId, fetchDocuments]);

  // Fetch draft documents (no orderReqId filter)
  const fetchDraftDocuments = useCallback(async () => {
    console.log('[fetchDraftDocuments] Called with:', { currentUserEmail });

    if (!currentUserEmail) {
      console.log('[fetchDraftDocuments] Skipped - missing currentUserEmail');
      return;
    }

    try {
      const params = new URLSearchParams({
        userEmail: currentUserEmail,
      });
       
      const url = `${PRESIGNED_DOCS_ENDPOINT}?${params.toString()}`;
      console.log('[fetchDraftDocuments] Fetching:', url);

      const resp = await fetch(url, {
        credentials: 'include',
      });

      console.log('[fetchDraftDocuments] Response status:', resp.status);

      if (!resp.ok) {
        console.warn('[fetchDraftDocuments] Failed to fetch draft documents:', resp.status);
        return;
      }

      const data = await resp.json();
      console.log('[fetchDraftDocuments] Response data:', data);

      const docs = data?.documents || [];
      console.log('[fetchDraftDocuments] Total draft documents:', docs.length);

      setDraftDocuments(docs);
    } catch (err) {
      console.error('[fetchDraftDocuments] Error fetching draft documents:', err);
    }
  }, [currentUserEmail]);

  // Fetch draft documents when currentUserEmail is available
  useEffect(() => {
    if (currentUserEmail) {
      fetchDraftDocuments();
    }
  }, [currentUserEmail, fetchDraftDocuments]);

  // Handle document download - fetch public URL and trigger download
  const handleDocumentDownload = async (doc: any) => {
    try {
      // POST to public-url endpoint to get download URL
      const resp = await fetch(PRESIGNED_PUBLIC_URL_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          s3_key: doc.s3_key || doc.key
        }),
      });

      if (!resp.ok) {
        throw new Error(`Failed to get public URL: ${resp.status}`);
      }

      const data = await resp.json();
      const publicUrl = data?.public_url;

      if (!publicUrl) {
        throw new Error('No public URL in response');
      }

      // Automatically trigger download by opening URL in new window
      window.open(publicUrl, '_blank');
    } catch (err: any) {
      console.error('Download error:', err);
      alert(`Failed to download document: ${err.message}`);
    }
  };

  // Handle attach selected draft documents to order
  const handleAttachDocuments = async () => {
    if (!orderReqId) {
      alert('Please create or select an order first');
      return;
    }

    if (selectedDraftDocs.size === 0) {
      alert('Please select at least one document to attach');
      return;
    }

    try {
      const attachPromises = Array.from(selectedDraftDocs).map(async (s3_key) => {
        const payload = {
          s3_key,
          order_req_id: String(orderReqId),
          user_email: currentUserEmail,
        };

        console.log('[handleAttachDocuments] Attaching:', payload);

        const resp = await fetch(PRESIGNED_ATTACH_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(payload),
        });

        if (!resp.ok) {
          const error = await resp.text();
          throw new Error(`Failed to attach ${s3_key}: ${resp.status} ${error}`);
        }

        return resp.json();
      });

      await Promise.all(attachPromises);

      alert(`Successfully attached ${selectedDraftDocs.size} document(s) to order ${orderReqId}`);

      // Clear selection
      setSelectedDraftDocs(new Set());

      // Refresh both document lists
      fetchDocuments();
      fetchDraftDocuments();
    } catch (err: any) {
      console.error('[handleAttachDocuments] Error:', err);
      alert(`Failed to attach documents: ${err.message}`);
    }
  };

  // Fetch list of industries on initial load
  useEffect(() => {
    const fetchIndustries = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/role-details/industries`);
        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }
        const data = await response.json();
        setIndustries(data);
      } catch (error) {
        console.error("Failed to fetch industries:", error);
        setApiError("Could not load industries. Please try again later.");
        setIndustries([]);
      }
    };
    fetchIndustries();
    // After fetching industries, check for pending Draft orders for current user
    const checkPendingOrders = async () => {
      try {
        const params = new URLSearchParams({ requestor_email: currentUserEmail, status: 'Draft' });
        const resp = await fetch(`${API_BASE_URL}/api/v1/order-req/search?${params.toString()}`);
        if (!resp.ok) {
          console.warn('search pending orders failed', resp.status);
          return;
        }
        const data = await resp.json();
        if (!Array.isArray(data)) return;
        if (data.length > 1) {
          setBlockedPendingMultiple(true);
          setApiError('Multiple pending records — check with Admin');
          return;
        }
        if (data.length === 1) {
          // populate the single order
          const orderRec = data[0];
          const orderId = orderRec?.OrderReqID || orderRec?.orderReqId || orderRec?.id || orderRec?._id;
          if (!orderId) return;
          setOrderReqId(orderId);
          try {
            const getResp = await fetch(`${API_BASE_URL}/api/v1/order-req/${orderId}`);
            if (!getResp.ok) {
              console.warn('Could not fetch existing order by id', orderId);
              return;
            }
            const orderData = await getResp.json();
            // populate delivery date (convert ISO -> YYYY-MM-DD for UI)
            const deliveryIso = orderData?.DeliveryDate || orderData?.deliveryDate;
            if (deliveryIso) {
              const asDate = new Date(deliveryIso);
              setExpectedDeliveryDate(asDate.toISOString().split('T')[0]);
            }
            const remoteProducts = orderData?.Products || orderData?.products || [];
            // try to determine industry name from orderData if present
            const industryName = orderData?.Industry || orderData?.industry || orderRec?.Industry || orderRec?.industry || 'Imported';
            const mappedProducts = (Array.isArray(remoteProducts) ? remoteProducts : []).map((rp: any) => ({
              id: Number(rp.ProductSeq ?? rp.productSeq ?? rp.ProductSeq) || Date.now(),
              productName: rp.ProductName || rp.productName || '',
              quantity: String(rp.Quantity ?? rp.quantity ?? ''),
              remarks: rp.Remarks || rp.remarks || '',
              factors: rp.factors || {},
            } as Product));
            setProducts(prev => ({ ...prev, [industryName]: mappedProducts }));
            // set selectedIndustry to the real industry definition so the EditFrame
            // renders the preference fields (factors). If fetching the role-details
            // fails, fall back to a minimal object.
            try {
              const indResp = await fetch(`${API_BASE_URL}/api/v1/role-details/by-industry/${encodeURIComponent(industryName)}`);
              if (indResp.ok) {
                const indData = await indResp.json();
                const industryData = Array.isArray(indData) ? indData[0] : indData;
                if (industryData) {
                  setSelectedIndustry(normalizeIndustry(industryData));
                } else {
                  setSelectedIndustry({ Industry: industryName, Scale: '', factorskey: {} } as Industry);
                }
              } else {
                setSelectedIndustry({ Industry: industryName, Scale: '', factorskey: {} } as Industry);
              }
            } catch (err) {
              console.warn('Failed to fetch industry details for populated order', err);
              setSelectedIndustry({ Industry: industryName, Scale: '', factorskey: {} } as Industry);
            }
            setApiError(null);
          } catch (err) {
            console.warn('Failed to populate single pending order', err);
          }
        }
      } catch (err) {
        console.warn('checkPendingOrders failed', err);
      }
    };
    checkPendingOrders();
  }, []);

  // Drag handlers for resizable divider
  useEffect(() => {
    if (!isDragging) return;
    const onMove = (e: MouseEvent | TouchEvent) => {
      const container = document.querySelector('.split-container') as HTMLElement | null;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const clientX = (e as TouchEvent).touches ? (e as TouchEvent).touches[0].clientX : (e as MouseEvent).clientX;
      let pct = ((clientX - rect.left) / rect.width) * 100;
      pct = Math.max(10, Math.min(80, pct)); // clamp between 10% and 80%
      setLeftWidth(pct);
      e.preventDefault?.();
    };

    const onUp = () => setIsDragging(false);
    window.addEventListener('mousemove', onMove as any);
    window.addEventListener('touchmove', onMove as any, { passive: false } as EventListenerOptions);
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchend', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove as any);
      window.removeEventListener('touchmove', onMove as any);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchend', onUp);
    };
  }, [isDragging]);

  const handleSelectIndustry = useCallback(async (industryName: string) => {
    if (!industryName) {
        setSelectedIndustry(null);
        return;
    }

    setApiError(null);
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/role-details/by-industry/${industryName}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`API Error: ${response.statusText} - ${errorData.detail}`);
        }
        const data = await response.json();
    const industryData = Array.isArray(data) ? data[0] : data;
    setSelectedIndustry(normalizeIndustry(industryData));
    } catch (error) {
        console.error("Failed to fetch industry data:", error);
        setApiError("Could not connect to the backend. Please try again later.");
        setSelectedIndustry(null);
    }
  }, []);


  // compute next ProductSeq by inspecting local products and (if available) the remote order's Products
  const computeNextProductSeq = async (): Promise<number> => {
    let maxSeq = 0;
    if (selectedIndustry) {
      const local = products[selectedIndustry.Industry] || [];
      local.forEach(p => {
        const n = Number(p.id || 0);
        if (!Number.isNaN(n)) maxSeq = Math.max(maxSeq, n);
      });
    }

    // If we have an orderReqId, try to fetch the remote order and include its ProductSeq values
    if (orderReqId) {
      try {
        const resp = await fetch(`${API_BASE_URL}/api/v1/order-req/${orderReqId}`);
        if (resp.ok) {
          const data = await resp.json();
          const remoteProducts = data?.Products || data?.products || [];
          if (Array.isArray(remoteProducts)) {
            remoteProducts.forEach((rp: any) => {
              const seq = Number(rp.ProductSeq ?? rp.productSeq ?? rp.ProductSeq);
              if (!Number.isNaN(seq)) maxSeq = Math.max(maxSeq, seq);
            });
          }
        }
      } catch (err) {
        // ignore remote fetch errors and fallback to local
        console.warn('Failed to fetch remote order for seq computation', err);
      }
    }

    // ensure at least 1
    return Math.max(1, maxSeq + 1);
  };

  // Convert the selected date (YYYY-MM-DD) into an ISO timestamp string for backend payloads.
  // Uses date-fns for deterministic parsing. By default this function attaches the current UTC time
  // to the chosen date and returns an ISO string. If you prefer midnight UTC, use formatDeliveryDateMidnightUTC.
  const formatDeliveryDateForPayload = (dateStr: string | null | undefined): string | null => {
    if (!dateStr) return null;
    try {
      // parseISO will parse YYYY-MM-DD as local-midnight, so we create a UTC-based date by combining
      // the date components with the current UTC time.
      const now = new Date();
      // construct an ISO-like string with dateStr and current UTC time, then parse
      const timePart = now.toISOString().slice(11); // "HH:mm:ss.sssZ"
      const combined = `${dateStr}T${timePart}`; // e.g. "2025-10-19T12:34:56.789Z"
  const parsed = parseISO(combined);
  return parsed.toISOString();
    } catch (err) {
      console.warn('formatDeliveryDateForPayload failed to parse date', dateStr, err);
      return null;
    }
  };

  // Alternative: return the date at midnight UTC (useful if backend expects date-only meaning the day)
  const formatDeliveryDateMidnightUTC = (dateStr: string | null | undefined): string | null => {
    if (!dateStr) return null;
    try {
      // parse just the date and set UTC midnight explicitly
  const parsedDate = parseISO(`${dateStr}T00:00:00Z`);
  return parsedDate.toISOString();
    } catch (err) {
      console.warn('formatDeliveryDateMidnightUTC failed to parse date', dateStr, err);
      return null;
    }
  };

  const handleAddNew = async () => {
    // require delivery date before allowing adding products
    if (!expectedDeliveryDate) {
      setApiError('Please select a Delivery Date before adding products.');
      return;
    }

    const nextId = await computeNextProductSeq();
    // keep productSeq state in sync for any fallback logic
    setProductSeq(nextId + 1);
    setEditingProduct({
      id: nextId,
      productName: '',
      quantity: '',
      remarks: '',
      factors: {},
    });
  };

  const handleEdit = (product: Product) => {
    // If an editor is already open, treat this click as pressing the inline 'X' first.
    (async () => {
      if (editingProduct) {
        const curr = editingProduct as Partial<Product>;
        // If current editor has no productName, close without saving and switch.
        if (!curr.productName || !curr.productName.trim()) {
          setEditingProduct(product);
          return;
        }

        // Validate mandatory fields before saving
        const validation = validateProductForSave(curr);
        if (!validation.ok) {
          setApiError(validation.message || 'Please complete required fields before switching items.');
          return; // do not switch
        }

        // Save current product (will POST/PUT) then switch to clicked product
        try {
          await handleSaveProduct(curr, { close: true });
          setEditingProduct(product);
        } catch (err: any) {
          setApiError(err?.message || 'Failed to save current product before switching.');
        }
        return;
      }

      setEditingProduct(product);
    })();
  };

  const handlePropose = (product: Product) => {
      setProposingProduct(product);
  };

  // Validate a product before saving: when productName present we ensure required
  // preference keys (industry factors ending with '*'), quantity is a positive number
  // (or non-empty) and remarks are present if industry defines them as required.
  const validateProductForSave = (p: Partial<Product>): { ok: boolean; message?: string } => {
    if (!p) return { ok: false, message: 'No product' };
    if (!p.productName || !p.productName.trim()) return { ok: false, message: 'Product Name is required.' };

    // Check required factor keys
    const requiredKeys = Object.keys(selectedIndustry?.factorskey || {}).filter(k => isRequired(k));
    const missing: string[] = [];
    requiredKeys.forEach(k => {
      const val = p.factors?.[k];
      const isEmpty = val === undefined || val === null || (typeof val === 'string' && !val.trim()) || (Array.isArray(val) && val.length === 0) || (typeof val === 'object' && Object.keys(val).length === 0);
      if (isEmpty) missing.push(getLabel(k));
    });
    if (missing.length > 0) return { ok: false, message: `Please complete required preferences: ${missing.join(', ')}` };

    // quantity: ensure non-empty and numeric-ish
    if (!p.quantity || !String(p.quantity).trim() || isNaN(Number(String(p.quantity).trim()))) return { ok: false, message: 'Quantity is required and must be a number.' };

    return { ok: true };
  };

  const handleCloseEditFrame = () => {
    setEditingProduct(null);
  };

  const handleCloseProposal = () => {
      setProposingProduct(null);
  };

  // Upsert product into products list. If options.close is true, close the editor after save.
  // Upsert product into products list. If options.close is true, close the editor after save
  // and synchronize the Order Request with the backend (POST for draft if not present, otherwise GET+PUT).
  const handleSaveProduct = async (productToSave: Partial<Product>, options?: { close?: boolean }) => {
    if (!selectedIndustry) return;

    const industryName = selectedIndustry.Industry;
    const currentProducts = products[industryName] || [];
    const existingProductIndex = currentProducts.findIndex(p => p.id === productToSave.id);

    if (existingProductIndex > -1) {
      const updatedProducts = [...currentProducts];
      updatedProducts[existingProductIndex] = { ...(updatedProducts[existingProductIndex] as Product), ...(productToSave as Product) } as Product;
      setProducts(prev => ({ ...prev, [industryName]: updatedProducts }));
    } else {
      setProducts(prev => ({
        ...prev,
        [industryName]: [...(prev[industryName] || []), productToSave as Product],
      }));
    }

    // After saving locally, if this save was triggered as a close action from the editor,
    // synchronize with the Order Request endpoint: create a Draft if none exists, otherwise fetch and update.
    if (options?.close) {
      try {
        // ensure delivery date is specified before sending to backend
        if (!expectedDeliveryDate) {
          setDeliveryDateError('Delivery Date is required before saving to order.');
          // still close editor locally but do not call backend
          handleCloseEditFrame();
          return;
        }

        // build the payload from current products for this industry
        const productsForPayload = (products[industryName] || []).concat(existingProductIndex === -1 ? [productToSave as Product] : []);

        const buildPayload = (status: string) => ({
          RequestorEmailID: currentUserEmail,
          OrderReqStatus: status,
          Industry: selectedIndustry?.Industry || '',
          Products: productsForPayload.map((p: Product) => ({
            ProductSeq: String(p.id),
            Quantity: String(Number(p.quantity) || 0),
            factors: p.factors || {},
            ProductName: p.productName || '',
          })),
          DeliveryDate: formatDeliveryDateMidnightUTC(expectedDeliveryDate),
        });

        // If we don't have an orderReqId yet, POST a draft
        if (!orderReqId) {
          const payload = buildPayload('Draft');
          const resp = await fetch(`${API_BASE_URL}/api/v1/order-req/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          if (!resp.ok) {
            const err = await resp.text();
            throw new Error(`Failed to create order request: ${resp.status} ${err}`);
          }
          const data = await resp.json();
          // expect returned object contains OrderReqID
          if (data?.OrderReqID) {
            setOrderReqId(data.OrderReqID);
          } else if (data?.orderReqId) {
            setOrderReqId(data.orderReqId);
          }
        } else {
          // If orderReqId exists, fetch it and PUT the updated payload
          // NOTE: endpoint shape: GET /api/v1/order-req/{order_req_id}
          // We GET first to follow the requested sequence, then PUT to update
          try {
            const getResp = await fetch(`${API_BASE_URL}/api/v1/order-req/${orderReqId}`);
            if (!getResp.ok) {
              console.warn('Could not fetch existing order request; proceeding to PUT anyway');
            }
          } catch (err) {
            console.warn('GET order-req failed', err);
          }

          const payload = buildPayload('Draft');
          const putResp = await fetch(`${API_BASE_URL}/api/v1/order-req/${orderReqId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          if (!putResp.ok) {
            const err = await putResp.text();
            throw new Error(`Failed to update order request: ${putResp.status} ${err}`);
          }
        }

        setApiError(null);
      } catch (err: any) {
        console.error(err);
        setApiError(err?.message || 'Order synchronization failed.');
      } finally {
        handleCloseEditFrame();
      }
    }
  };

  // Delete a product by id
  const handleDeleteProduct = (productId: number) => {
    if (!selectedIndustry) return;
    const industryName = selectedIndustry.Industry;
    const currentProducts = products[industryName] || [];
    setProducts(prev => ({ ...prev, [industryName]: currentProducts.filter(p => p.id !== productId) }));
    // If the deleted product is currently being edited, close the editor
    if (editingProduct?.id === productId) {
      setEditingProduct(null);
    }
  };

  const currentProducts = useMemo(() => {
    return selectedIndustry ? products[selectedIndustry.Industry] || [] : [];
  }, [selectedIndustry, products]);

  const today = new Date().toISOString().split('T')[0];

  const handleLogout = async () => {
    try {
      const response = await fetch('/auth/logout?returnTo=' + encodeURIComponent(window.location.origin), {
        method: 'POST',
        credentials: 'include'
      });

      const data = await response.json();

      // If Keycloak logout URL provided, redirect there to end SSO session
      if (data.keycloakLogoutUrl) {
        window.location.href = data.keycloakLogoutUrl;
      } else {
        // Fallback: just redirect to home
        window.location.href = '/';
      }
    } catch (err) {
      console.error('Logout failed:', err);
      window.location.href = '/';
    }
  };

  return (
    <div className="container mx-auto p-4 md:p-8">
      {/* Auth check: show loading, login page, or welcome screen */}
      {isAuthenticated === null && (
        <div className="text-center py-20">
          <p className="text-lg text-gray-600">Checking authentication...</p>
        </div>
      )}

      {isAuthenticated === false && (
        <Login />
      )}

      {isAuthenticated === true && !showApp && (
        <Welcome
          onOpenApp={() => setShowApp(true)}
          onViewSubmittedOrders={() => {
            // TODO: Implement view submitted orders logic
            console.log('View Submitted Orders clicked - logic to be implemented');
          }}
        />
      )}

      {isAuthenticated === true && showApp && (
        <>
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-gray-800">Order Form</h1>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowApp(false)}
            className="py-2 px-4 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
          >
            Back to Home
          </button>
          <button
            onClick={handleLogout}
            className="py-2 px-4 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      {apiError && (
          <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6" role="alert">
            <p className="font-bold">Backend Alert</p>
            <p>{apiError}</p>
          </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
          <div>
            <select
              id="industry"
              name="industry"
              aria-label="Choose Order type"
              value={selectedIndustry?.Industry || ''}
              onChange={(e) => handleSelectIndustry(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              disabled={blockedPendingMultiple || !!orderReqId}
            >
              <option value="">Choose order type</option>
              {industries.map(ind => (
                <option key={ind} value={ind}>{ind}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="deliveryDate" className="block text-sm font-medium text-gray-700 mb-1">Expected Delivery Date <span className="text-red-500">*</span></label>
            <input
              type="date"
              id="deliveryDate"
              name="deliveryDate"
              value={expectedDeliveryDate}
              min={today}
              onChange={(e) => { setExpectedDeliveryDate(e.target.value); setApiError(null); setDeliveryDateError(null); }}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            {deliveryDateError && (
              <p className="text-sm text-red-600 mt-1">{deliveryDateError}</p>
            )}
          </div>
        </div>
      </div>

  {/* Order level actions: Submit / Cancel (only show when at least one product exists) */}
  {currentProducts.length > 0 && (
  <div className="mb-6 flex items-center justify-end space-x-3">
        <button
          type="button"
          onClick={async () => {
            if (blockedPendingMultiple) {
              setApiError('Multiple pending Draft orders exist for your account. Please contact Admin.');
              return;
            }
            // Submit order: require at least one product and delivery date
            if (!selectedIndustry) {
              setApiError('Please select an industry before submitting an order.');
              return;
            }
            const industryName = selectedIndustry.Industry;
            const currentProducts = products[industryName] || [];
            if (currentProducts.length === 0) {
              setApiError('At least one product is required to submit an order.');
              return;
            }
            if (!expectedDeliveryDate) {
              setApiError('Delivery Date is required before submitting.');
              return;
            }

            try {
              const payload = {
                RequestorEmailID: currentUserEmail,
                OrderReqStatus: 'Submitted',
                Products: currentProducts.map((p: Product) => ({ ProductSeq: String(p.id), Quantity: String(Number(p.quantity) || 0), factors: p.factors || {}, ProductName: p.productName || '' })),
                DeliveryDate: formatDeliveryDateMidnightUTC(expectedDeliveryDate),
              };

              // If orderReqId doesn't exist, POST and set it; otherwise PUT
              if (!orderReqId) {
                const resp = await fetch(`${API_BASE_URL}/api/v1/order-req/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                if (!resp.ok) throw new Error(`Submit failed: ${resp.status}`);
                const data = await resp.json();
                const newId = data?.OrderReqID || data?.orderReqId || null;
                setOrderReqId(newId);
                alert(`Order Submitted : ${newId}`);
                window.location.reload();
              } else {
                const resp = await fetch(`${API_BASE_URL}/api/v1/order-req/${orderReqId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                if (!resp.ok) throw new Error(`Submit (update) failed: ${resp.status}`);
                alert(`Order Submitted : ${orderReqId}`);
                window.location.reload();
              }

              setApiError(null);
              alert('Order submitted successfully');
            } catch (err: any) {
              console.error(err);
              setApiError(err?.message || 'Order submit failed.');
            }
          }}
          className="py-2 px-3 bg-green-600 text-white font-semibold rounded-lg shadow-md hover:bg-green-700 focus:outline-none text-sm"
        >
          Submit Order
        </button>

        <button
          type="button"
          onClick={async () => {
              if (blockedPendingMultiple) {
                setApiError('Multiple pending Draft orders exist for your account. Please contact Admin.');
                return;
              }
            if (!orderReqId) {
              setApiError('No order exists to cancel.');
              return;
            }
            try {
              // Either call DELETE or emulate cancel via PUT with status 'Cancelled'
              // confirm cancel with user
              const confirmCancel = window.confirm('Are you sure you want to cancel this order?');
              if (!confirmCancel) return;
              const resp = await fetch(`${API_BASE_URL}/api/v1/order-req/${orderReqId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ OrderReqStatus: 'Cancelled' }) });
              if (!resp.ok) {
                // try delete as fallback
                const del = await fetch(`${API_BASE_URL}/api/v1/order-req/${orderReqId}`, { method: 'DELETE' });
                if (!del.ok) throw new Error(`Cancel failed: ${del.status}`);
              }
              setOrderReqId(null);
              setApiError(null);
              alert(`Order Cancelled : ${orderReqId}`);
              window.location.reload();
            } catch (err: any) {
              console.error(err);
              setApiError(err?.message || 'Order cancel failed.');
            }
          }}
          className="py-2 px-3 bg-red-600 text-white font-semibold rounded-lg shadow-md hover:bg-red-700 focus:outline-none text-sm"
        >
          Cancel Order
        </button>
      </div>
      )}

      {/* Upload button visible only when at least one product exists */}
      {currentProducts.length > 0 && (
        <div className="mb-6">
          <label className="inline-flex items-center space-x-2">
            <input id="fileInput" type="file" accept="application/pdf,image/jpeg" style={{ display: 'none' }} onChange={async (e) => {
              const file = (e.target as HTMLInputElement).files?.[0];
              if (!file) return;
              // basic checks
              if (file.size > 2 * 1024 * 1024) { setApiError('File must be < 2 MB'); return; }
              const allowed = ['application/pdf','image/jpeg'];
              if (!allowed.includes(file.type)) { setApiError('Only PDF and JPG allowed'); return; }
              if (!orderReqId) { setApiError('No OrderReq ID available. Save or create an order first.'); return; }
              setApiError(null);
              setUploading(true);

              // helper: compute SHA-256 hex checksum
              const computeChecksum = async (f: File) => {
                const buf = await f.arrayBuffer();
                const hash = await crypto.subtle.digest('SHA-256', buf);
                const arr = Array.from(new Uint8Array(hash));
                return arr.map(b => b.toString(16).padStart(2, '0')).join('');
              };

              try {
                const checksum = await computeChecksum(file);

                // Build the presign request body according to requested schema.
                // Only include config_name when it is non-empty — some backends
                // treat the config identifier as optional and will derive policy
                // from other fields (order id, file type, etc.).
                const presignBody: any = {
                  order_req_id: String(orderReqId),
                  file_name: file.name,
                  content_type: file.type,
                  file_size: file.size,
                  label: `Label ${file.name}`,
                  notes: `Uploaded by finance team for Order ${orderReqId}`,
                  checksum,
                };
                if (PRESIGNED_URL_CONFIG_NAME && PRESIGNED_URL_CONFIG_NAME.toString().trim()) {
                  presignBody.config_name = PRESIGNED_URL_CONFIG_NAME;
                }

                // Request presigned POST data from backend
                const presignResp = await fetch(PRESIGNED_URL_ENDPOINT, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(presignBody),
                  credentials: 'include', // Send auth cookies for Keycloak authentication
                });

                if (!presignResp.ok) {
                  const txt = await presignResp.text().catch(() => '');
                  throw new Error(`Presign request failed: ${presignResp.status} ${txt}`);
                }

                const presignData = await presignResp.json();
                const presignedUrl = presignData?.presigned_url || presignData?.presignedUrl || presignData?.url;
                const uploadFields = presignData?.upload_fields || presignData?.uploadFields || presignData?.fields;
                if (!presignedUrl || !uploadFields) {
                  throw new Error('Invalid presign response: missing presigned_url or upload_fields');
                }

                // Build multipart/form-data body for the presigned POST
                const form = new FormData();
                // Append all upload fields returned by backend
                Object.entries(uploadFields).forEach(([k, v]) => {
                  // ensure values are strings
                  form.append(k, String(v));
                });
                // Append meta fields expected by S3; some servers expect file field name 'file'
                form.append('file', file);

                // POST the form to the S3 presigned url
                const uploadResp = await fetch(presignedUrl, { method: 'POST', body: form });
                if (!(uploadResp.ok || uploadResp.status === 204)) {
                  const txt = await uploadResp.text().catch(() => '');
                  throw new Error(`Upload to presigned URL failed: ${uploadResp.status} ${txt}`);
                }

                // Success - Call status endpoint to update document status
                const s3_key = presignData?.s3_key || presignData?.key;
                if (s3_key) {
                  try {
                    await fetch(`${PRESIGNED_STATUS_ENDPOINT}/${s3_key}`, {
                      method: 'PUT',
                      credentials: 'include',
                    });
                  } catch (statusErr) {
                    console.warn('Status update failed:', statusErr);
                    // Don't throw - upload was successful even if status update failed
                  }
                }

                alert('File uploaded successfully');
                // Refresh documents lists
                if (orderReqId) {
                  fetchDocuments();
                }
                fetchDraftDocuments();
              } catch (err: any) {
                console.error(err);
                setApiError(err?.message || 'Upload failed');
              } finally {
                setUploading(false);
                try { (document.getElementById('fileInput') as HTMLInputElement).value = ''; } catch(_) {}
              }
            }} />
            <button onClick={() => { (document.getElementById('fileInput') as HTMLInputElement).click(); }} disabled={uploading} className={`py-2 px-3 bg-blue-600 text-white rounded-md ${uploading ? 'opacity-60 cursor-not-allowed' : 'hover:bg-blue-700'}`}>
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
            <span className="text-sm text-gray-500">Allowed: .pdf, .jpg — File &lt; 2 MB — Not password-protected</span>
          </label>
        </div>
      )}

      {/* Documents sections */}
      <div className="mb-6 space-y-4">
        {/* Order Docs - Only show when orderReqId exists */}
        {orderReqId && (
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
            <div
              className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50"
              onClick={() => setIsOrderDocsOpen(!isOrderDocsOpen)}
            >
              <h3 className="text-lg font-semibold text-gray-700">
                Order Docs ({documents.length})
              </h3>
              <svg
                className={`w-5 h-5 text-gray-600 transform transition-transform ${isOrderDocsOpen ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            {isOrderDocsOpen && (
              <div className="border-t border-gray-200">
                {documents.length > 0 ? (
                  <ul className="divide-y divide-gray-200">
                    {documents.map((doc: any, idx: number) => (
                      <li
                        key={idx}
                        className="px-4 py-3 hover:bg-blue-50 transition cursor-pointer"
                        onClick={() => handleDocumentDownload(doc)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">
                              {doc.file_name || doc.label || `Document ${idx + 1}`}
                            </p>
                            {doc.label && doc.label !== doc.file_name && (
                              <p className="text-xs text-gray-500 mt-1">{doc.label}</p>
                            )}
                            {doc.notes && (
                              <p className="text-xs text-gray-500 mt-1">{doc.notes}</p>
                            )}
                          </div>
                          <div className="ml-4 flex items-center space-x-2">
                            {doc.upload_status && (
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                doc.upload_status === 'Completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {doc.upload_status}
                              </span>
                            )}
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="px-4 py-6 text-center">
                    <p className="text-sm text-gray-500">No order documents yet</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Draft Docs - Always visible when user is authenticated */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1 cursor-pointer hover:bg-gray-50" onClick={() => setIsDraftDocsOpen(!isDraftDocsOpen)}>
              <h3 className="text-lg font-semibold text-gray-700">
                Draft Docs ({draftDocuments.length})
              </h3>
              <svg
                className={`w-5 h-5 text-gray-600 transform transition-transform ${isDraftDocsOpen ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            {orderReqId && selectedDraftDocs.size > 0 && (
              <button
                onClick={handleAttachDocuments}
                className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 transition-colors"
              >
                Attach ({selectedDraftDocs.size})
              </button>
            )}
          </div>
          {isDraftDocsOpen && (
            <div className="border-t border-gray-200">
              {draftDocuments.length > 0 ? (
                <ul className="divide-y divide-gray-200">
                  {draftDocuments.map((doc: any, idx: number) => {
                    const s3Key = doc.s3_key || doc.key || '';
                    const isSelected = selectedDraftDocs.has(s3Key);

                    return (
                      <li
                        key={idx}
                        className="px-4 py-3 hover:bg-blue-50 transition"
                      >
                        <div className="flex items-center space-x-3">
                          {/* Checkbox for selection */}
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              e.stopPropagation();
                              const newSelection = new Set(selectedDraftDocs);
                              if (e.target.checked) {
                                newSelection.add(s3Key);
                              } else {
                                newSelection.delete(s3Key);
                              }
                              setSelectedDraftDocs(newSelection);
                            }}
                            className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                          />

                          {/* Document info - clickable for download */}
                          <div
                            className="flex items-center justify-between flex-1 cursor-pointer"
                            onClick={() => handleDocumentDownload(doc)}
                          >
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">
                                {doc.file_name || doc.label || `Document ${idx + 1}`}
                              </p>
                              {doc.label && doc.label !== doc.file_name && (
                                <p className="text-xs text-gray-500 mt-1">{doc.label}</p>
                              )}
                              {doc.notes && (
                                <p className="text-xs text-gray-500 mt-1">{doc.notes}</p>
                              )}
                            </div>
                            <div className="ml-4 flex items-center space-x-2">
                              {doc.upload_status && (
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  doc.upload_status === 'Completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {doc.upload_status}
                                </span>
                              )}
                              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                            </div>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <div className="px-4 py-6 text-center">
                  <p className="text-sm text-gray-500">No draft documents yet</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {selectedIndustry && (
        <div className="split-container flex gap-4 relative">
          {/* Left column: products list (resizable) */}
          <div className="left-panel" style={{ width: editingProduct ? `${leftWidth}%` : '100%' }}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold text-gray-700">Products {currentProducts.length > 0 ? `(${currentProducts.length})` : ''}</h2>
              {!editingProduct && (
                <button
                  onClick={handleAddNew}
                  disabled={!expectedDeliveryDate}
                  title={!expectedDeliveryDate ? 'Select Delivery Date before adding products' : 'Add new product'}
                  className={`py-2 px-3 font-semibold rounded-lg shadow-md text-sm ${!expectedDeliveryDate ? 'bg-gray-300 text-gray-600 cursor-not-allowed' : 'bg-indigo-600 text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-75'}`}
                >
                  + Add
                </button>
              )}

              {blockedPendingMultiple && (
                <div className="mt-2 text-sm text-red-600">Multiple pending Draft orders found for {currentUserEmail}. Check with Admin — creation is blocked.</div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <ul className="divide-y divide-gray-200">
                {currentProducts.length > 0 ? (
                  currentProducts.map(product => (
                    <li key={product.id} className="p-4 hover:bg-gray-50 flex justify-between items-center">
                      <div>
                          <p className="text-lg font-medium text-indigo-600">{product.productName}</p>
                          <p className="text-sm text-gray-500">Qty: {product.quantity || 'N/A'}</p>
                      </div>
                      <div className="flex space-x-2 items-center">
                        {/* When editingProduct is active hide all action buttons per request */}
                          {!editingProduct && (
                          <>
                            <button onClick={() => handleEdit(product)} className="text-sm text-blue-600 hover:text-blue-800">Edit</button>
                            <button onClick={() => handleDeleteProduct(product.id)} className="text-sm text-red-600 hover:text-red-800" title="Delete">Delete</button>
                          </>
                        )}
                      </div>
                    </li>
                  ))
                ) : (
                  <li className="p-4 text-center text-gray-500">No products added yet for this industry.</li>
                )}
              </ul>
            </div>
          </div>

          {/* Divider - only show when editor open */}
          {editingProduct && (
            <div
              className="divider bg-gray-200 cursor-col-resize"
              style={{ width: '8px', cursor: 'col-resize' }}
              onMouseDown={() => setIsDragging(true)}
              onTouchStart={() => setIsDragging(true)}
            />
          )}

          {/* Right column: inline editor (visible when editingProduct) */}
          {editingProduct && (
            <div className="right-panel" style={{ width: `${100 - leftWidth}%` }}>
              <EditFrame
                industry={selectedIndustry}
                product={editingProduct}
                onSave={handleSaveProduct}
                onClose={handleCloseEditFrame}
                validateForSave={validateProductForSave}
                inline={true}
              />
            </div>
          )}
        </div>
      )}

      {/* Inline editor is rendered in the split layout above. Remove duplicate modal rendering. */}

      {/* Proposal flow commented out */}
        </>
      )}
    </div>
  );
};

export default App;
