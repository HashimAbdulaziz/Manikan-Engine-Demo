import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getProductById } from '../data/products'
import ManikanWidget from '../components/ManikanWidget'

/* ─────────────────────────────────────────────────────────────────────────
   Product Detail Page — Full product view with Manikan widget integration
   ───────────────────────────────────────────────────────────────────────── */
export default function ProductDetailPage() {
  const { id } = useParams()
  const product = getProductById(id)
  const [showWidget, setShowWidget] = useState(false)
  const [selectedSize, setSelectedSize] = useState('M')

  if (!product) {
    return (
      <div className="pdp-not-found">
        <h2>Product not found</h2>
        <Link to="/" className="pdp-back-link">← Back to Store</Link>
      </div>
    )
  }

  const sizeKeys = Object.keys(product.sizes)
  const currentSpecs = product.sizes[selectedSize]

  return (
    <div className="pdp-page">
      {/* ── Navigation ────────────────────────────────────────────────── */}
      <nav className="pdp-nav">
        <Link to="/" className="pdp-nav-back" id="back-to-store">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Store</span>
        </Link>
        <div className="pdp-nav-brand">
          <span className="store-footer-logo" style={{ fontSize: '14px' }}>THREADCRAFT</span>
        </div>
      </nav>

      {/* ── Product Content ───────────────────────────────────────────── */}
      <div className="pdp-content">
        {/* Left — Product Image */}
        <div className="pdp-image-section">
          <div className="pdp-image-wrap">
            <img src={product.image} alt={product.name} className="pdp-image" />
          </div>
        </div>

        {/* Right — Product Details */}
        <div className="pdp-details-section">
          <div className="pdp-details-inner">
            {/* Color badge */}
            <div className="pdp-color-badge">
              <div className="pdp-color-dot" style={{ background: product.color_hex }} />
              <span>{product.color_name}</span>
            </div>

            <h1 className="pdp-title" id="product-title">{product.name}</h1>
            <p className="pdp-price">${product.price.toFixed(2)}</p>
            <p className="pdp-description">{product.description}</p>

            {/* ── Size Selector ──────────────────────────────────────── */}
            <div className="pdp-size-section">
              <h3 className="pdp-section-label">Select Size</h3>
              <div className="pdp-size-pills">
                {sizeKeys.map(size => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`pdp-size-pill ${selectedSize === size ? 'active' : ''}`}
                    id={`size-${size}`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            {/* ── Size Chart ─────────────────────────────────────────── */}
            <div className="pdp-chart-section">
              <h3 className="pdp-section-label">Garment Measurements</h3>
              <div className="pdp-chart">
                <div className="pdp-chart-row">
                  <span className="pdp-chart-label">Chest Width</span>
                  <span className="pdp-chart-value">{currentSpecs.chest_width_cm} cm</span>
                </div>
                <div className="pdp-chart-row">
                  <span className="pdp-chart-label">Body Length</span>
                  <span className="pdp-chart-value">{currentSpecs.body_length_cm} cm</span>
                </div>
                <div className="pdp-chart-row">
                  <span className="pdp-chart-label">Sleeve Length</span>
                  <span className="pdp-chart-value">{currentSpecs.sleeve_length_cm} cm</span>
                </div>
                <div className="pdp-chart-row">
                  <span className="pdp-chart-label">Shoulder Width</span>
                  <span className="pdp-chart-value">{currentSpecs.shoulder_width_cm} cm</span>
                </div>
              </div>
            </div>

            {/* ── Manikan Try-On Button ───────────────────────────────── */}
            <button
              onClick={() => setShowWidget(true)}
              className="pdp-tryon-btn"
              id="try-on-button"
            >
              <div className="pdp-tryon-btn-icon">
                <span className="manikan-logo-sm">M</span>
              </div>
              <div className="pdp-tryon-btn-text">
                <span className="pdp-tryon-btn-main">Try On with Manikan</span>
                <span className="pdp-tryon-btn-sub">See how it fits your body in 3D</span>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>

            {/* ── Add to Cart ────────────────────────────────────────── */}
            <button className="pdp-cart-btn" id="add-to-cart">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
              </svg>
              Add to Cart — ${product.price.toFixed(2)}
            </button>
          </div>
        </div>
      </div>

      {/* ── Manikan Widget Modal ─────────────────────────────────────── */}
      {showWidget && (
        <ManikanWidget
          product={product}
          onClose={() => setShowWidget(false)}
        />
      )}
    </div>
  )
}
