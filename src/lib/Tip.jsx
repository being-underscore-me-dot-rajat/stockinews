export default function Tip({ text }) {
    return (
        <span className="info-tip" data-tooltip={text} tabIndex="0" aria-label={text}>ℹ</span>
    );
}
