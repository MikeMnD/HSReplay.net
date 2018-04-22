import React from "react";
import PropTypes from "prop-types";
import InfoIcon, { InfoIconProps } from "../InfoIcon";
import UserData from "../../UserData";
import { image } from "../../helpers";
import Modal from "../Modal";
import PremiumModal from "./PremiumModal";

interface Props {
	analyticsLabel: string;
	iconStyle?: any;
	infoHeader?: InfoIconProps["header"];
	infoContent?: InfoIconProps["content"];
}

interface State {
	hovering: boolean;
	triggered: PremiumWrapper[];
	touchCount: number;
	showModal: boolean;
}

const key = "hsreplaynet_premium_wrappers";

export default class PremiumWrapper extends React.Component<Props, State> {
	constructor(props: Props, context: any) {
		super(props, context);
		this.state = {
			hovering: false,
			touchCount: 0,
			triggered: [],
			showModal: false,
		};
	}

	static childContextTypes = {
		requiresPremium: PropTypes.bool,
	};

	getChildContext() {
		return { requiresPremium: true };
	}

	public trigger(wrapper: PremiumWrapper) {
		if (wrapper === this) {
			return;
		}
		this.setState((state, props) => ({
			touchCount: 0,
			triggered: state.triggered.concat([wrapper]),
		}));
	}

	public release(wrapper: PremiumWrapper) {
		if (wrapper === this) {
			return;
		}
		this.setState((state, props) => ({
			triggered: state.triggered.filter(
				(toRemove: PremiumWrapper) => toRemove !== wrapper,
			),
		}));
	}

	public componentDidMount(): void {
		// register to global list of premium wrappers
		if (typeof window[key] === "undefined") {
			window[key] = [];
		}
		window[key].push(this);
	}

	public componentWillUnmount(): void {
		if (typeof window[key] === "undefined") {
			return;
		}
		window[key].forEach((wrapper: PremiumWrapper) => {
			wrapper.release(this);
		});
		window[key] = window[key].filter(
			(component: PremiumWrapper) => component !== this,
		);
	}

	public componentDidUpdate(
		prevProps: Readonly<Props>,
		prevState: Readonly<State>,
		prevContext: any,
	): void {
		if (prevState.hovering === this.state.hovering) {
			return;
		}
		// hover is starting or ending
		window[key].forEach((wrapper: PremiumWrapper) => {
			if (this.state.hovering) {
				wrapper.trigger(this);
			} else {
				wrapper.release(this);
			}
		});
	}

	public render(): React.ReactNode {
		const {
			analyticsLabel,
			iconStyle,
			infoHeader,
			infoContent,
			children,
			...childProps
		} = this.props;

		let infoIcon = null;
		if (this.props.infoHeader) {
			infoIcon = <InfoIcon header={infoHeader} content={infoContent} />;
		}

		const classNames = ["premium-wrapper"];
		if (this.shouldAppear()) {
			classNames.push("visible");
		}
		if (this.state.hovering || this.state.triggered.length > 0) {
			classNames.push("hovering");
		}

		return (
			<>
				<Modal
					visible={this.state.showModal}
					onClose={() => this.setState({ showModal: false })}
				>
					<PremiumModal analyticsLabel={analyticsLabel} />
				</Modal>
				<div
					className={classNames.join(" ")}
					onTouchStart={() =>
						this.setState({
							hovering: true,
							touchCount: this.state.touchCount + 1,
						})
					}
					onTouchCancel={() => this.setState({ hovering: false })}
					onClick={event => {
						if (event && event.currentTarget) {
							event.currentTarget.blur();
						}
						if (!this.shouldAppear()) {
							return;
						}
						if (this.state.touchCount % 2 === 1) {
							return;
						}
						this.setState({ showModal: true });
					}}
					onMouseEnter={() => this.setState({ hovering: true })}
					onMouseLeave={() =>
						this.setState({ hovering: false, touchCount: 0 })
					}
					onFocus={() => this.setState({ hovering: true })}
					onBlur={() => this.setState({ hovering: false })}
					onKeyPress={event => {
						if (event.which !== 13) {
							return;
						}
						if (!this.shouldAppear()) {
							return;
						}
						this.setState({ showModal: true });
					}}
					tabIndex={this.shouldAppear() ? 0 : -1}
				>
					<img
						className="premium-icon"
						src={image("premium.png")}
						style={iconStyle}
						role="presentation"
					/>
					{infoIcon}
					<div className="premium-info">
						<h4>
							Get <span className="text-premium">Premium</span>
						</h4>
						{this.state.touchCount > 0 ? (
							<span>Tap for more details…</span>
						) : null}
					</div>
					{React.Children.map(
						children,
						(child: React.ReactElement<any>) =>
							React.cloneElement(
								child,
								Object.assign({}, childProps, child.props),
							),
					)}
				</div>
			</>
		);
	}

	protected shouldAppear() {
		return !UserData.isPremium();
	}
}