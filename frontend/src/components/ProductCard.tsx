import { Smartphone, Zap, Star, ChevronRight } from 'lucide-react';

interface ProductCardProps {
    product: {
        id: number;
        name: string;
        brand: string;
        price: number;
        key_specs: {
            [key: string]: string;
        };
        highlights: string[];
    };
}

export default function ProductCard({ product }: ProductCardProps) {
    const formatPrice = (price: number) => {
        return `₹${price.toLocaleString('en-IN')}`;
    };

    return (
        <div className="group relative rounded-2xl bg-[#18181b] border border-[#27272a] hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-900/10 transition-all duration-300 overflow-hidden flex flex-col h-full">
            {/* Glossy gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

            {/* Header */}
            <div className="p-4 sm:p-5 flex-1 relative z-10">
                <div className="flex items-start justify-between mb-3 sm:mb-4">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {product.brand}
                    </span>
                    <div className="flex items-center gap-1 bg-[#27272a] px-2 py-1 rounded-lg">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                        <span className="text-xs font-medium text-gray-300">4.{Math.floor(Math.random() * 5 + 4)}</span>
                    </div>
                </div>

                <h3 className="text-base sm:text-lg font-bold text-white mb-2 line-clamp-2 leading-tight group-hover:text-blue-400 transition-colors">
                    {product.name}
                </h3>

                <div className="text-xl sm:text-2xl font-black text-white mb-1 tracking-tight">
                    {formatPrice(product.price)}
                    <span className="text-[10px] sm:text-xs font-normal text-gray-500 ml-2 align-middle">avg. market price</span>
                </div>

                {/* Specs Grid */}
                <div className="grid grid-cols-2 gap-2 mt-3 sm:mt-4">
                    {Object.entries(product.key_specs).slice(0, 4).map(([key, value], idx) => (
                        <div key={idx} className="bg-[#09090b] rounded-lg p-2 border border-[#27272a]">
                            <p className="text-[10px] text-gray-500 uppercase font-semibold mb-0.5">{key}</p>
                            <p className="text-xs text-gray-200 font-medium truncate" title={value}>{value}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className="p-3 sm:p-4 bg-[#09090b] border-t border-[#27272a] relative z-10">
                <button className="w-full py-3 sm:py-2.5 rounded-xl bg-white text-black font-bold text-sm hover:bg-gray-200 transition-colors flex items-center justify-center gap-2 group-hover:shadow-lg min-h-[44px]">
                    View Details
                    <ChevronRight className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}
